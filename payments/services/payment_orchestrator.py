# payments/services/payment_orchestrator.py

from django.utils import timezone
from django.db import transaction as db_txn
from django.core.exceptions import ValidationError
import logging
from typing import Dict, Any, Optional

from payments.services.scheduled_payment_service import ScheduledPaymentService
from payments.services.bulk_payment_service import BulkPaymentService  
from payments.services.payment_link_service import PaymentLinkService
from payments.services.payment_report_service import PaymentReportService
from payments.services.payment_service import PaymentService
from payments.gateways.registry import get_gateway

from security.helpers.alerts import send_slack_alert

logger = logging.getLogger(__name__)


class PaymentOrchestrator:
    """
    Central orchestrator for coordinating payment services and gateways.
    """

    def __init__(self):
        self.scheduled_service = ScheduledPaymentService()
        self.bulk_service = BulkPaymentService()
        self.link_service = PaymentLinkService()
        self.report_service = PaymentReportService()
        self.payment_service = PaymentService()

    # ---------------- Daily Tasks ----------------
    def execute_daily_tasks(self) -> Dict[str, Any]:
        results = {}
        try:
            results['scheduled_payments'] = self.scheduled_service.execute_due_payments()
            results['bulk_payments'] = self.bulk_service.process_pending_executions()
            results['expired_links'] = self.link_service.cleanup_expired_links()
            results['daily_reports'] = self.report_service.generate_daily_summaries()
            logger.info("Daily payment tasks completed successfully")
            return results
        except Exception as e:
            logger.exception("Daily payment tasks failed")
            send_slack_alert(f"[PaymentOrchestrator] Daily tasks failed: {e}")
            raise

    # ---------------- Gateway Orchestration ----------------
    def route_payment(self, *, user, amount, payment_method, invoice=None, metadata=None, request=None):
        """
        Route a payment to the correct gateway (pawapay, stripe, flutterwave, wallet)
        """
        try:
            gateway_name = self.payment_service._get_gateway_from_method(payment_method)
            logger.info(f"Routing payment via gateway={gateway_name}")
            
            result = self.payment_service.process_payment(
                user=user,
                amount=amount,
                payment_method=payment_method,
                invoice=invoice,
                metadata=metadata or {},
                request=request
            )
            return result

        except ValidationError as ve:
            logger.warning(f"Payment validation error: {ve}")
            send_slack_alert(f"[Payment Validation Error] {ve}")
            raise
        except Exception as e:
            logger.exception("Payment routing failed")
            send_slack_alert(f"[PaymentOrchestrator] Routing failed: {e}")
            raise

    # ---------------- Resilience Layer ----------------
    def retry_failed_transactions(self, limit: int = 10) -> int:
        """
        Retry previously failed transactions (within limit)
        """
        from jamiiwallet.models.transaction import Transaction
        failed = Transaction.objects.filter(
            status=Transaction.TransactionStatus.FAILED,
            created_at__gte=timezone.now() - timezone.timedelta(days=2)
        )[:limit]

        retried = 0
        for txn in failed:
            try:
                gw_name = (txn.receipt or {}).get("provider")
                if not gw_name:
                    continue
                gw = get_gateway(gw_name)
                resp = gw.check_transaction_status(transaction_id=txn.idempotency_key)
                logger.info(f"Retry check for txn={txn.reference} status={resp.get('status')}")
                self.payment_service.poll_transaction_status(txn, gw_name)
                retried += 1
            except Exception as e:
                logger.error(f"Retry failed for txn={txn.reference}: {e}")
                send_slack_alert(f"[Retry Failed] txn={txn.reference} error={e}")
        return retried