# jamiitasks/tasks/payment_tasks.py

import math
import logging
import traceback
import time
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db import transaction as db_txn
from django.contrib.auth import get_user_model

from celery import shared_task, current_app
from celery.exceptions import MaxRetriesExceededError, Retry
from jamiikazini.celery import app as celery_app  # your celery app

from payments.services.payment_orchestrator import PaymentOrchestrator
from payments.services.scheduled_payment_service import ScheduledPaymentService
from payments.services.bulk_payment_service import BulkPaymentService
from payments.services.payment_link_service import PaymentLinkService
from payments.services.payment_report_service import PaymentReportService

from jamiiwallet.models.transaction import Transaction
from payments.models.payment_failure import PaymentFailure
from jamiiwallet.models.wallet import Wallet
from jamiitasks.services.payment_gateway import initiate_topup
from jamiiwallet.services.transaction_engine import TransactionEngine
from payments.models.bulk_payment import BulkPaymentExecution, BulkPaymentTemplate

from jamiitasks.services.dead_letter_service import DeadLetterService
from jamiitasks.config.throttling import THROTTLE_LIMITS

logger = logging.getLogger(__name__)
User = get_user_model()


# ------------------------
# Helpers: throttling + logging + DLQ
# ------------------------

def _apply_rate_limit_for_task(task_name: str):
    """
    Apply per-task dynamic rate limit (best-effort).
    Uses THROTTLE_LIMITS mapping (task_name -> "<count>/m").
    Called at task start so we adapt even if limits changed.
    """
    try:
        limit = THROTTLE_LIMITS.get(task_name)
        if limit:
            try:
                # apply to current app (best-effort)
                current_app.control.rate_limit(task_name, limit)
                logger.debug(f"[Throttle] Applied rate limit {limit} → {task_name}")
            except Exception as e:
                logger.warning(f"[Throttle] Could not apply rate limit {limit} for {task_name}: {e}")
    except Exception:
        logger.exception("Error while applying rate limit")


def _safe_log_execution(task_name: str, task_id: str, payload: dict, status: str, extra: dict = None):
    """
    Try to persist an execution log to TaskExecutionLog if model exists.
    Otherwise fallback to structured logger.
    """
    extra = extra or {}
    try:
        # Try to import model if present
        from jamiitasks.models.task_log import TaskExecutionLog  # optional model
        TaskExecutionLog.objects.create(
            task_name=task_name,
            task_id=task_id,
            payload=payload or {},
            status=status,
            metadata=extra.get("metadata", {}),
            started_at=extra.get("started_at"),
            finished_at=extra.get("finished_at"),
            error=extra.get("error")
        )
    except Exception:
        # fallback to logger
        if status == "STARTED":
            logger.info(f"[TaskLog][START] {task_name} id={task_id} payload={payload}")
        elif status == "SUCCESS":
            logger.info(f"[TaskLog][SUCCESS] {task_name} id={task_id} payload={payload} extra={extra}")
        else:
            logger.error(f"[TaskLog][{status}] {task_name} id={task_id} payload={payload} extra={extra}")


def _push_to_dlq(task_name: str, task_id: str, payload: dict, exc: Exception, tb: str = None, attempts: int = 0, metadata: dict = None):
    try:
        ds = DeadLetterService()
        ds.push(
            task_name=task_name,
            task_id=task_id,
            payload=payload or {},
            error=str(exc),
            traceback=tb or (getattr(exc, "__traceback__", None) and "".join(traceback.format_tb(exc.__traceback__))),
            attempts=attempts or 0,
            metadata=metadata or {}
        )
        logger.warning(f"[DLQ] Pushed {task_name} id={task_id} attempts={attempts}")
    except Exception:
        logger.exception("Failed to push to DLQ")


def _compute_backoff(retries: int, base: int = 5, cap: int = 3600):
    """Exponential backoff: min(base * 2^retries, cap)"""
    try:
        delay = min(base * (2 ** retries), cap)
        return delay
    except Exception:
        return base


# ------------------------
# Tasks
# ------------------------

@shared_task(name="payment_tasks.execute_daily_payment_automation")
def execute_daily_payment_automation():
    """Daily automation for all payment features"""
    task_name = execute_daily_payment_automation.name
    task_id = f"local-{int(time.time())}"
    payload = {}
    _apply_rate_limit_for_task(task_name)
    _safe_log_execution(task_name, task_id, payload, "STARTED", {"started_at": timezone.now()})
    try:
        orchestrator = PaymentOrchestrator()
        results = orchestrator.execute_daily_tasks()
        _safe_log_execution(task_name, task_id, payload, "SUCCESS", {"finished_at": timezone.now(), "metadata": {"result": results}})
        logger.info(f"Daily payment automation completed: {results}")
        return results
    except Exception as e:
        tb = traceback.format_exc()
        _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": str(e)})
        logger.exception("Daily payment automation failed")
        raise


@celery_app.task(bind=True, max_retries=5, name="payment_tasks.process_scheduled_payment")
def process_scheduled_payment(self, payment_id):
    """
    Process a scheduled payment with retry logic + DeadLetterService fallback.
    This task uses celery_app.task (bound) to ensure it's registered with the project celery app.
    """
    task_name = self.name
    task_id = self.request.id
    payload = {"args": [payment_id], "kwargs": {}}
    _apply_rate_limit_for_task(task_name)
    _safe_log_execution(task_name, task_id, payload, "STARTED", {"started_at": timezone.now()})

    try:
        service = ScheduledPaymentService()
        service.execute(payment_id)
        _safe_log_execution(task_name, task_id, payload, "SUCCESS", {"finished_at": timezone.now()})
        logger.info(f"[ScheduledPayment] Payment {payment_id} executed successfully.")
        return {"status": "SUCCESS", "payment_id": payment_id}

    except Exception as exc:
        # exponential backoff
        retries = getattr(self.request, "retries", 0)
        countdown = _compute_backoff(retries, base=30, cap=3600)
        logger.warning(
            f"[ScheduledPayment] Retry {retries + 1}/{self.max_retries} for {payment_id} after {countdown}s due to {exc}"
        )
        tb = traceback.format_exc()

        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            # push to DLQ
            _push_to_dlq(
                task_name=task_name,
                task_id=task_id,
                payload=payload,
                exc=exc,
                tb=tb,
                attempts=self.max_retries,
                metadata={"alert_on_fail": True, "source": "payment_tasks", "payment_id": payment_id}
            )
            _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": str(exc)})
            logger.error(f"[ScheduledPayment] Max retries exceeded for {payment_id}, moved to DLQ.")
            return {"status": "FAILED", "payment_id": payment_id, "error": str(exc)}


@shared_task(name="payment_tasks.cleanup_expired_payment_links")
def cleanup_expired_payment_links():
    """Mark expired payment links as expired"""
    task_name = cleanup_expired_payment_links.name
    task_id = f"local-{int(time.time())}"
    payload = {}
    _apply_rate_limit_for_task(task_name)
    _safe_log_execution(task_name, task_id, payload, "STARTED", {"started_at": timezone.now()})
    try:
        service = PaymentLinkService()
        results = service.cleanup_expired_links()
        _safe_log_execution(task_name, task_id, payload, "SUCCESS", {"finished_at": timezone.now(), "metadata": {"result": results}})
        logger.info(f"Expired payment links cleaned up: {results}")
        return results
    except Exception as e:
        tb = traceback.format_exc()
        _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": str(e)})
        logger.exception("Payment links cleanup failed")
        raise


@shared_task(bind=True, name="payment_tasks.initiate_topup")
def initiate_topup(self, user_id, amount):
    """
    Celery task to initiate a top-up in the background.
    """
    task_name = self.name
    task_id = self.request.id
    payload = {"args": [user_id, amount], "kwargs": {}}
    _apply_rate_limit_for_task(task_name)
    _safe_log_execution(task_name, task_id, payload, "STARTED", {"started_at": timezone.now()})

    try:
        user = User.objects.get(pk=user_id)
        txn = initiate_topup(user=user, amount=amount)
        TransactionEngine.process(txn)
        _safe_log_execution(task_name, task_id, payload, "SUCCESS", {"finished_at": timezone.now(), "metadata": {"reference": getattr(txn, "reference", None)}})
        return {"reference": txn.reference, "status": txn.status}
    except Exception as exc:
        tb = traceback.format_exc()
        logger.error(f"[TopUp Task] Error: {exc}", exc_info=True)
        try:
            raise self.retry(exc=exc, countdown=_compute_backoff(getattr(self.request, "retries", 0), base=10))
        except MaxRetriesExceededError:
            _push_to_dlq(task_name=task_name, task_id=task_id, payload=payload, exc=exc, tb=tb, attempts=self.max_retries, metadata={"source": "initiate_topup"})
            _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": str(exc)})
            return {"error": str(exc)}


@shared_task(bind=True, name="payment_tasks.verify_transaction")
def verify_transaction(self, reference):
    """
    Task to check the current status of a transaction.
    """
    task_name = self.name
    task_id = self.request.id
    payload = {"args": [reference], "kwargs": {}}
    _apply_rate_limit_for_task(task_name)
    _safe_log_execution(task_name, task_id, payload, "STARTED", {"started_at": timezone.now()})

    try:
        txn = Transaction.objects.get(reference=reference)
        _safe_log_execution(task_name, task_id, payload, "SUCCESS", {"finished_at": timezone.now(), "metadata": {"status": txn.status}})
        return {"reference": reference, "status": txn.status}
    except Transaction.DoesNotExist:
        logger.error(f"[Verify Task] Transaction {reference} not found.")
        _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": "NOT_FOUND"})
        return {"reference": reference, "status": "NOT_FOUND"}
    except Exception as exc:
        tb = traceback.format_exc()
        logger.error(f"[Verify Task] Error verifying {reference}: {exc}", exc_info=True)
        try:
            raise self.retry(exc=exc, countdown=_compute_backoff(getattr(self.request, "retries", 0), base=10))
        except MaxRetriesExceededError:
            _push_to_dlq(task_name=task_name, task_id=task_id, payload=payload, exc=exc, tb=tb, attempts=self.max_retries, metadata={"source": "verify_transaction"})
            _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": str(exc)})
            return {"reference": reference, "status": "ERROR"}


@shared_task(name="payment_tasks.retry_failed_topups")
def retry_failed_topups():
    """Retry all failed top-up transactions by reprocessing them."""
    task_name = retry_failed_topups.name
    task_id = f"local-{int(time.time())}"
    payload = {}
    _apply_rate_limit_for_task(task_name)
    _safe_log_execution(task_name, task_id, payload, "STARTED", {"started_at": timezone.now()})

    failed_txns = Transaction.objects.filter(
        transaction_type=Transaction.TransactionType.TOP_UP,
        status=Transaction.TransactionStatus.FAILED,
    )
    retried_count = 0
    for txn in failed_txns:
        try:
            TransactionEngine.process(txn)
            retried_count += 1
        except Exception as e:
            logger.warning(f"[Retry Task] Could not retry {txn.reference}: {e}")
            continue

    _safe_log_execution(task_name, task_id, payload, "SUCCESS", {"finished_at": timezone.now(), "metadata": {"retried": retried_count}})
    return f"Retried {retried_count} failed top-up(s)."


@shared_task(bind=True, max_retries=5, name="payment_tasks.process_payment")
def process_payment(self, user_id, amount, reference, payment_type="standard"):
    """
    Enhanced payment task that supports different payment types
    """
    task_name = self.name
    task_id = self.request.id
    payload = {"args": [user_id, str(amount), reference, payment_type], "kwargs": {}}
    _apply_rate_limit_for_task(task_name)
    _safe_log_execution(task_name, task_id, payload, "STARTED", {"started_at": timezone.now()})

    try:
        with db_txn.atomic():
            wallet = Wallet.objects.select_for_update().get(user_id=user_id)

            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))

            if wallet.balance < amount:
                logger.warning(f"[Payment] Insufficient balance for user {user_id} reference {reference}")
                raise self.retry(
                    exc=ValueError("Insufficient balance"),
                    countdown=_compute_backoff(getattr(self.request, "retries", 0), base=5)
                )

            wallet.balance -= amount
            wallet.save()

            _safe_log_execution(task_name, task_id, payload, "SUCCESS", {"finished_at": timezone.now(), "metadata": {"reference": reference}})
            logger.info(f"Payment {reference} ({payment_type}) for user {user_id} processed successfully")
            return {"success": True, "type": payment_type}

    except Retry:
        # Retry halali ya celery - iachie worker (except Exception isiikamate)
        raise

    except (MaxRetriesExceededError, Exception) as exc:
        # KUMBUKA: retry(exc=...) ikiisha retries, celery hurusha exc YENYEWE
        # (si MaxRetriesExceededError) - kwa hivyo tunakagua retries wenyewe.
        tb = traceback.format_exc()
        retries = getattr(self.request, "retries", 0)
        max_retries = getattr(self, "max_retries", 0) or 0
        logger.warning(f"Retry {retries} for payment {reference} failed: {exc}")

        if not isinstance(exc, MaxRetriesExceededError) and retries < max_retries:
            raise self.retry(exc=exc, countdown=_compute_backoff(retries, base=5))

        # Retries zimeisha - permanent failure: rekodi + DLQ
        # NB: PaymentFailure model haina field 'metadata'
        try:
            PaymentFailure.objects.create(
                user_id=user_id,
                amount=amount,
                reference=reference,
                reason=str(exc) or "Insufficient balance or persistent error",
                retries=max_retries,
            )
        except Exception:
            logger.exception("Failed to create PaymentFailure record")

        _push_to_dlq(task_name=task_name, task_id=task_id, payload=payload, exc=exc, tb=tb, attempts=max_retries, metadata={"source": "process_payment"})
        _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": str(exc)})

        logger.error(f"Payment {reference} ({payment_type}) failed permanently")
        return {"success": False, "type": payment_type}


@shared_task(name="payment_tasks.retry_failed_payments")
def retry_failed_payments():
    """
    Enhanced retry task that includes new payment types
    """
    task_name = retry_failed_payments.name
    task_id = f"local-{int(time.time())}"
    payload = {}
    _apply_rate_limit_for_task(task_name)
    _safe_log_execution(task_name, task_id, payload, "STARTED", {"started_at": timezone.now()})

    failures = PaymentFailure.objects.filter(retries__lt=getattr(settings, "PAYMENT_SYSTEM", {}).get("MAX_PAYMENT_RETRIES", 5)).order_by('created_at')
    retried_count = 0

    for failure in failures:
        try:
            payment_type = failure.metadata.get('payment_type', 'standard') if failure.metadata else 'standard'
            # call as async apply so concurrency respects queues & throttles
            async_res = process_payment.apply_async(args=(
                failure.user_id,
                float(failure.amount),
                failure.reference,
                payment_type
            ))
            # Optionally check result (not blocking)
            retried_count += 1
            logger.info(f"Retried (enqueued) payment failure {failure.reference} via task {async_res.id}")
        except Exception as e:
            failure.increment_retries()
            logger.error(f"Exception retrying payment failure {failure.reference}: {e}")

    _safe_log_execution(task_name, task_id, payload, "SUCCESS", {"finished_at": timezone.now(), "metadata": {"retried": retried_count}})
    logger.info(f"Retried {retried_count} failed payment(s).")
    return f"Retried {retried_count} failed payment(s)."


@shared_task(bind=True, name="payment_tasks.notify_wallet_balance_change", max_retries=3)
def notify_wallet_balance_change(self, wallet_id, user_id, new_balance):
    """
    Notify other systems about wallet balance change.
    """
    task_name = self.name
    task_id = self.request.id
    payload = {"args": [str(wallet_id), user_id, str(new_balance)], "kwargs": {}}
    _apply_rate_limit_for_task(task_name)
    _safe_log_execution(task_name, task_id, payload, "STARTED", {"started_at": timezone.now()})

    try:
        logger.info(f"Balance change for wallet {wallet_id} (User: {user_id}) → {new_balance}")
        _safe_log_execution(task_name, task_id, payload, "SUCCESS", {"finished_at": timezone.now()})
        return True
    except Exception as exc:
        tb = traceback.format_exc()
        logger.error(f"Error notifying balance change: {exc}", exc_info=True)
        try:
            raise self.retry(exc=exc, countdown=_compute_backoff(getattr(self.request, "retries", 0), base=5))
        except MaxRetriesExceededError:
            _push_to_dlq(task_name=task_name, task_id=task_id, payload=payload, exc=exc, tb=tb, attempts=self.max_retries, metadata={"source": "notify_wallet_balance_change"})
            _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": str(exc)})
            return False


@shared_task(bind=True, name="payment_tasks.process_bulk_payment_task", max_retries=3, acks_late=True)
def process_bulk_payment_task(self, execution_id):
    """
    Celery task to process a BulkPaymentExecution.
    - Loads payments from template (preferred) or execution.metadata['ad_hoc_payments_data'].
    - Processes in chunks to control memory and DB locks.
    - Uses select_for_update() on wallets to avoid races.
    - Updates execution progress & handles partial failures.
    """
    task_name = self.name
    task_id = self.request.id
    payload = {"args": [execution_id], "kwargs": {}}
    _apply_rate_limit_for_task(task_name)
    _safe_log_execution(task_name, task_id, payload, "STARTED", {"started_at": timezone.now()})

    try:
        execution = BulkPaymentExecution.objects.select_related("template", "executed_by").get(id=execution_id)
    except BulkPaymentExecution.DoesNotExist:
        logger.error("BulkPaymentExecution %s not found", execution_id)
        _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": "NOT_FOUND"})
        return {"execution_id": execution_id, "status": "NOT_FOUND"}

    # Prevent double-processing
    if execution.status not in [BulkPaymentExecution.Status.PROCESSING]:
        logger.warning("Execution %s not in PROCESSING state (current=%s). Aborting.", execution.id, execution.status)
        _safe_log_execution(task_name, task_id, payload, "SKIPPED", {"finished_at": timezone.now(), "metadata": {"current_status": execution.status}})
        return {"execution_id": execution_id, "status": "SKIPPED", "current_status": execution.status}

    # Load payments list
    payments = None
    if execution.template_id:
        template = BulkPaymentTemplate.objects.filter(id=execution.template_id).first()
        payments = template.payments_data if template else None
    else:
        payments = execution.metadata.get("ad_hoc_payments_data") if execution.metadata else None

    if not payments:
        execution.status = BulkPaymentExecution.Status.FAILED
        execution.results = {"error": "No payments data found"}
        execution.completed_at = timezone.now()
        execution.save(update_fields=["status", "results", "completed_at"])
        logger.error("Execution %s has no payments data.", execution.id)
        _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": "no payments"})
        return {"execution_id": execution_id, "status": "FAILED", "error": "no payments"}

    total = len(payments)
    success_count = 0
    failed_count = 0
    results = []

    # chunk size: tuneable via settings
    CHUNK_SIZE = getattr(settings, "BULK_PAYMENT_CHUNK_SIZE", 100)

    try:
        # iterate in chunks to limit DB locking
        num_chunks = math.ceil(total / CHUNK_SIZE)
        for chunk_idx in range(num_chunks):
            start = chunk_idx * CHUNK_SIZE
            end = start + CHUNK_SIZE
            chunk = payments[start:end]

            # Process each item in the chunk; we try to minimize the duration of select_for_update locks
            for item in chunk:
                recipient_id = item.get("recipient_user_id") or item.get("recipient_id")
                amount = Decimal(str(item.get("amount", "0")))
                reference = item.get("reference") or f"BULK-{execution.id}-{recipient_id}-{start}"
                metadata = item.get("metadata", {})

                try:
                    # Fetch recipient wallet and lock for update for safe balance operations
                    with db_txn.atomic():
                        recipient_wallet = Wallet.objects.select_for_update().get(user_id=recipient_id)

                        # Use TransactionEngine to create/process a transfer to recipient wallet
                        txn = TransactionEngine.create_transfer(
                            to_wallet=recipient_wallet,
                            amount=amount,
                            initiated_by_id=execution.executed_by_id,
                            reference=reference,
                            metadata=metadata
                        )

                        # TransactionEngine should return a transaction obj with status
                        success_count += 1
                        results.append({
                            "recipient": recipient_id,
                            "status": "SUCCESS",
                            "txn_ref": getattr(txn, "reference", None),
                            "amount": str(amount)
                        })

                except Exception as e_item:
                    failed_count += 1
                    logger.exception("Bulk payment failed for execution=%s recipient=%s: %s", execution.id, recipient_id, str(e_item))
                    results.append({
                        "recipient": recipient_id,
                        "status": "FAILED",
                        "error": str(e_item),
                        "amount": str(amount)
                    })
                    # optionally record PaymentFailure for manual inspection / retry logic
                    try:
                        PaymentFailure.objects.create(
                            user_id=recipient_id,
                            amount=amount,
                            reference=reference,
                            reason=str(e_item),
                            retries=0,
                            metadata={"bulk_execution_id": str(execution.id), **(metadata or {})}
                        )
                    except Exception:
                        logger.exception("Failed to create PaymentFailure for %s", recipient_id)

            # Update progress after each chunk
            execution.successful_count = (execution.successful_count or 0) + success_count
            execution.failed_count = (execution.failed_count or 0) + failed_count
            # progress percentage
            processed = execution.successful_count + execution.failed_count
            execution_progress = round((processed / total) * 100, 2) if total else 100.0
            execution.results = (execution.results or []) + results
            execution.save(update_fields=["successful_count", "failed_count", "results"])
            # reset local counters for next chunk accumulation (we already aggregated to execution)
            success_count = 0
            failed_count = 0
            results = []

        # finalize
        processed_total = (execution.successful_count or 0) + (execution.failed_count or 0)
        if processed_total == total and execution.failed_count == 0:
            execution.status = BulkPaymentExecution.Status.COMPLETED
        elif processed_total == total and execution.failed_count > 0:
            execution.status = BulkPaymentExecution.Status.PARTIAL
        else:
            # not all processed -> mark as FAILED
            execution.status = BulkPaymentExecution.Status.FAILED

        execution.completed_at = timezone.now()
        # option: compute success_rate
        execution.success_rate = round(((execution.successful_count or 0) / total) * 100, 2) if total else 0.0
        execution.save(update_fields=["status", "completed_at", "success_rate", "results", "successful_count", "failed_count"])

        logger.info("Bulk execution %s done -> %s/%s successful", execution.id, execution.successful_count, total)
        _safe_log_execution(task_name, task_id, payload, "SUCCESS", {"finished_at": timezone.now(), "metadata": {"successful": execution.successful_count, "failed": execution.failed_count}})
        return {"execution_id": execution_id, "status": "COMPLETED", "successful": execution.successful_count, "failed": execution.failed_count}

    except Exception as exc:
        tb = traceback.format_exc()
        logger.exception("Critical error processing bulk execution %s: %s", execution.id, str(exc))
        # Mark execution failed for operator visibility
        execution.status = BulkPaymentExecution.Status.FAILED
        execution.results = {"error": str(exc)}
        execution.completed_at = timezone.now()
        execution.save(update_fields=["status", "results", "completed_at"])
        # Retry with exponential backoff
        try:
            countdown = _compute_backoff(getattr(self.request, "retries", 0), base=5, cap=3600)
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error("Max retries exceeded for bulk execution %s", execution.id)
            _push_to_dlq(task_name=task_name, task_id=task_id, payload=payload, exc=exc, tb=tb, attempts=self.max_retries, metadata={"source": "process_bulk_payment_task", "execution_id": str(execution.id)})
            _safe_log_execution(task_name, task_id, payload, "FAILED", {"finished_at": timezone.now(), "error": str(exc)})
            return {"execution_id": execution_id, "status": "FAILED", "error": str(exc)}