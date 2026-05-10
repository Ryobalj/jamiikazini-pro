# jamiitasks/tasks/distributed_payment_tasks.py

import logging
import traceback
from django.utils import timezone
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.core.cache import cache

from payments.services.scheduled_payment_service import ScheduledPaymentService
from jamiitasks.services.dead_letter_service import DeadLetterService
from jamiiwallet.models.transaction import Transaction
from jamiitasks.tasks.payments_gateway_tasks import poll_transaction_status

logger = logging.getLogger(__name__)

CLAIM_TTL_SECONDS = 60  # seconds

def _compute_backoff(retries: int, base: int = 30, cap: int = 3600):
    return min(base * (2 ** retries), cap)

def _push_to_dlq(task_name, task_id, payload, exc, tb=None):
    try:
        ds = DeadLetterService()
        ds.push(
            task_name=task_name,
            task_id=task_id,
            payload=payload or {},
            error=str(exc),
            traceback=tb or (getattr(exc, "__traceback__", None) and "".join(traceback.format_tb(exc.__traceback__))),
            attempts=0
        )
        logger.warning(f"[DLQ] Pushed {task_name} id={task_id}")
    except Exception:
        logger.exception("Failed to push to DLQ")


def _claim_scheduled_payment(payment_id: str) -> bool:
    key = f"distributed_scheduled_payment_claim:{payment_id}"
    try:
        return cache.add(key, "1", timeout=CLAIM_TTL_SECONDS)
    except Exception:
        logger.exception(f"Failed to claim payment {payment_id}, skipping")
        return False


@shared_task(bind=True, name="distributed_payment_tasks.process_scheduled_payments", max_retries=3)
def process_scheduled_payments(self):
    task_name = self.name
    task_id = getattr(self.request, "id", f"local-{timezone.now().timestamp()}")
    payload = {}

    try:
        service = ScheduledPaymentService()
        due_payments = service.get_due_payments()  # list of payment dicts/IDs

        processed = []
        skipped = []

        for payment in due_payments:
            payment_id = str(payment["id"])
            if not _claim_scheduled_payment(payment_id):
                skipped.append(payment_id)
                continue

            try:
                txn: Transaction = service.execute_payment(payment)  # returns Transaction instance
                processed.append({"id": payment_id, "txn_ref": txn.reference, "status": txn.status})
                logger.info(f"[{task_name}] executed payment {payment_id} → {txn.status}")

                # enqueue poll for pending transactions
                if txn.status == Transaction.TransactionStatus.PENDING:
                    try:
                        poll_transaction_status.apply_async(
                            args=(txn.reference,),  # adapt if your task signature uses gateway/provider too
                            kwargs={"txn_id": str(txn.id)},
                            queue="payments"
                        )
                        logger.info(f"[{task_name}] enqueued poll for txn={txn.reference}")
                    except Exception:
                        logger.exception(f"Failed to enqueue poll for txn {txn.reference}")

            except Exception as exc:
                tb = traceback.format_exc()
                logger.exception(f"[{task_name}] error executing payment {payment_id}: {exc}")
                _push_to_dlq(task_name, task_id, {"payment_id": payment_id}, exc, tb)

        logger.info(f"[{task_name}] finished. processed={len(processed)}, skipped={len(skipped)}")
        return {"status": "OK", "processed": processed, "skipped": skipped, "total_due": len(due_payments)}

    except Exception as exc:
        tb = traceback.format_exc()
        logger.exception(f"[{task_name}] fatal error: {exc}")
        try:
            retries = getattr(self.request, "retries", 0)
            countdown = _compute_backoff(retries)
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            _push_to_dlq(task_name, task_id, payload, exc, tb)
            return {"status": "FAILED", "error": str(exc)}