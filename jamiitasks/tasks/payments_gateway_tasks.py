# jamiitasks/tasks/payments_gateway_tasks.py

from __future__ import annotations
import logging
import traceback
from typing import Optional, Tuple, Dict, Any

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from jamiiwallet.models.transaction import Transaction
from jamiitasks.services.dead_letter_service import DeadLetterService
from jamiitasks.utils.task_logger import TaskLogger
from payments.models.audit_log import AuditLog, AuditAction
from jamiiwallet.services.transaction_engine import TransactionEngine
from datetime import timedelta

logger = logging.getLogger(__name__)

# ==============================
# CONFIGURATION / CONSTANTS
# ==============================
POLL_PENDING_CHUNK_SIZE = getattr(settings, "POLL_PENDING_CHUNK_SIZE", 100)
POLL_PENDING_MAX_PER_RUN = getattr(settings, "POLL_PENDING_MAX_PER_RUN", 1000)
POLL_PENDING_LOCK_TTL = getattr(settings, "POLL_PENDING_LOCK_TTL", 60)
POLL_PENDING_AGE_SECONDS = getattr(settings, "POLL_PENDING_MIN_AGE_SECONDS", 10)

FAILOVER_AGE_MINUTES = getattr(settings, "FAILOVER_AGE_MINUTES", 5)
COMPENSATION_AGE_MINUTES = getattr(settings, "COMPENSATION_AGE_MINUTES", 10)


def _txn_claim_key(txn_id: int) -> str:
    return f"poll:txn:claim:{txn_id}"


def _compute_backoff(retry_count: int) -> int:
    """Exponential backoff helper."""
    return min((2 ** retry_count) * 60, 3600)


# ==============================
# HELPER: extract poll args
# ==============================
def _extract_poll_args_from_transaction(txn: Transaction) -> Optional[Tuple[str, str, str, Dict[str, Any]]]:
    """Extract (gateway_name, provider_id, txn_ref, extra_meta) from metadata or receipt."""
    metadata = getattr(txn, "metadata", {}) or {}
    receipt = txn.receipt or {}

    def pick(keys, source):
        for k in keys:
            v = source.get(k)
            if v:
                return str(v)
        return None

    gateway = pick(["gateway", "gateway_name", "provider"], metadata) or pick(["gateway", "gateway_name"], receipt)
    provider_id = pick(["provider_id", "provider_ref"], metadata) or pick(["provider_id", "provider_ref"], receipt)
    txn_ref = pick(["external_ref", "txn_ref", "provider_txn_ref", "reference"], metadata) or txn.reference

    if gateway and provider_id and txn_ref:
        return (
            gateway.lower(),
            str(provider_id),
            str(txn_ref),
            {
                "txn_id": str(txn.id),
                "transaction_reference": txn.reference,
                "created_at": txn.created_at.isoformat(),
                "transaction_type": txn.transaction_type,
            },
        )
    return None


# ==============================
# TASK 1: Poll transaction status
# ==============================
@shared_task(bind=True, max_retries=6, default_retry_delay=60)
def poll_transaction_status(self, gateway_name: str, provider_id: str, txn_ref: str) -> str:
    """
    Poll transaction status from provider and reconcile via PaymentService.
    Retries if still pending.
    """
    task_name = self.name
    task_id = self.request.id

    TaskLogger.log(task_name=task_name, status="STARTED", desc=f"Polling {txn_ref}", ref=txn_ref, task_id=task_id)

    try:
        from payments.services.payment_service import PaymentService

        txn = Transaction.objects.get(reference=txn_ref)
        new_status = PaymentService.poll_transaction_status(txn, gateway_name)

        if new_status == Transaction.TransactionStatus.PENDING:
            TaskLogger.log(
                task_name=task_name,
                status="RETRYING",
                desc=f"Still pending... retry #{self.request.retries + 1}",
                ref=txn_ref,
                task_id=task_id,
            )
            raise self.retry(countdown=(2 ** self.request.retries) * 60)

        logger.info("Polling complete for txn=%s provider_id=%s status=%s", txn_ref, provider_id, new_status)
        TaskLogger.log(task_name=task_name, status="SUCCESS", desc=f"Polling complete → {new_status}", ref=txn_ref, task_id=task_id)
        return new_status

    except Transaction.DoesNotExist:
        msg = f"Transaction not found: {txn_ref}"
        logger.warning(msg)
        TaskLogger.log(task_name=task_name, status="NOT_FOUND", desc=msg, ref=txn_ref, task_id=task_id)
        return "NOT_FOUND"

    except Exception as e:
        msg = f"Polling error txn={txn_ref}, gateway={gateway_name}: {e}"
        logger.error(msg, exc_info=True)
        TaskLogger.log(task_name=task_name, status="FAILED", desc=msg, ref=txn_ref, task_id=task_id)
        raise self.retry(exc=e)


# ==============================
# TASK 2: Failover handling
# ==============================
@shared_task(bind=True, name="payments_gateway_tasks.failover_wallet_payment")
def failover_wallet_payment(self):
    """
    Retry all failed or stuck wallet payments before triggering compensation.
    """
    cutoff = timezone.now() - timedelta(minutes=FAILOVER_AGE_MINUTES)

    stuck_txns = Transaction.objects.filter(
        transaction_type=Transaction.TransactionType.PAYMENT,
        status=Transaction.TransactionStatus.PENDING,
        created_at__lt=cutoff
    )

    logger.info(f"[Failover] Found {stuck_txns.count()} stuck payment(s) older than {FAILOVER_AGE_MINUTES} minutes")

    for txn in stuck_txns:
        try:
            logger.warning(f"[Failover] Retrying stuck payment {txn.id}")
            TransactionEngine.process(txn)

            AuditLog.log_action(
                user=txn.user,
                action=AuditAction.PAYMENT_RETRY,
                target_obj=txn,
                description=f"Retried stuck payment {txn.id} successfully",
                metadata={"txn_id": str(txn.id), "status": txn.status},
            )

        except Exception as e:
            logger.error(f"[Failover] Retry failed for txn {txn.id}: {e}", exc_info=True)
            compensate_stuck_transactions.apply_async(args=(txn.id,))


@shared_task(bind=True, name="payments_gateway_tasks.compensate_stuck_transactions")
def compensate_stuck_transactions(self, txn_id: Optional[int] = None):
    """
    Compensate stuck or delayed transactions automatically if retries fail.
    If txn_id is provided, compensates that specific transaction.
    """
    try:
        if txn_id:
            txns = Transaction.objects.filter(id=txn_id)
        else:
            cutoff = timezone.now() - timedelta(minutes=COMPENSATION_AGE_MINUTES)
            txns = Transaction.objects.filter(
                status=Transaction.TransactionStatus.PENDING,
                created_at__lt=cutoff
            )

        logger.info(f"[Compensate] Checking {txns.count()} transaction(s) for compensation")

        for txn in txns:
            try:
                logger.warning(f"[Compensate] Initiating refund for stuck txn {txn.id}")

                refund_meta = {"source_txn_id": txn.id}
                refund_txn = Transaction.objects.create(
                    user=txn.user,
                    amount=txn.amount,
                    transaction_type=Transaction.TransactionType.REFUND,
                    status=Transaction.TransactionStatus.PENDING,
                    metadata=refund_meta
                )

                TransactionEngine.process(refund_txn)

                AuditLog.log_action(
                    user=txn.user,
                    action=AuditAction.UPDATE,
                    target_obj=refund_txn,
                    description=f"Refund created for stuck txn {txn.id}",
                    metadata={"source_txn": str(txn.id), "refund_id": str(refund_txn.id)},
                )

                logger.info(f"[Compensate] Refund txn {refund_txn.id} processed for {txn.id}")

            except Exception as e:
                logger.error(f"[Compensate] Failed refund for txn {txn.id}: {e}", exc_info=True)

    except Exception as outer_e:
        logger.critical(f"[Compensate] Global failure: {outer_e}", exc_info=True)


# ==============================
# TASK 3: Poll pending transactions dispatcher
# ==============================
@shared_task(bind=True, name="payments_gateway_tasks.poll_pending_transactions", max_retries=3)
def poll_pending_transactions(self):
    """
    Dispatch `poll_transaction_status` tasks for all PENDING transactions.
    Uses cache-based claiming to avoid duplicates.
    """
    task_name = self.name
    task_id = getattr(self.request, "id", f"local-{timezone.now().timestamp()}")
    logger.info(f"[{task_name}] starting id={task_id}")

    try:
        cutoff = timezone.now() - timedelta(seconds=POLL_PENDING_AGE_SECONDS)
        qs = Transaction.objects.filter(
            status=Transaction.TransactionStatus.PENDING,
            created_at__lte=cutoff
        ).order_by("created_at")

        total = qs.count()
        if total == 0:
            logger.debug(f"[{task_name}] no pending transactions older than {POLL_PENDING_AGE_SECONDS}s")
            return {"status": "OK", "processed": 0, "skipped": 0}

        processed, skipped = 0, 0
        max_allowed = min(POLL_PENDING_MAX_PER_RUN, total)

        for txn in qs[:max_allowed]:
            claim_key = _txn_claim_key(txn.id)
            try:
                claimed = cache.add(claim_key, "1", timeout=POLL_PENDING_LOCK_TTL)
            except Exception:
                logger.exception(f"[{task_name}] cache.add failed for txn={txn.id}")
                skipped += 1
                continue

            if not claimed:
                skipped += 1
                continue

            args = _extract_poll_args_from_transaction(txn)
            if not args:
                logger.warning(f"[{task_name}] txn {txn.id} missing gateway/provider/ref, skipping.")
                AuditLog.log_action(
                    user=txn.initiated_by,
                    action=AuditAction.OTHER,
                    target_obj=txn,
                    description="Missing gateway/provider/ref for automated polling",
                    metadata={"txn_id": str(txn.id), "created_at": txn.created_at.isoformat()},
                )
                cache.delete(claim_key)
                skipped += 1
                continue

            gateway, provider_id, external_ref, meta = args
            try:
                poll_transaction_status.apply_async(args=(gateway, provider_id, external_ref), queue="payments")
                logger.info(f"[{task_name}] Enqueued poll for txn={txn.id} ({gateway}/{provider_id}/{external_ref})")
                processed += 1
                AuditLog.log_action(
                    user=txn.initiated_by,
                    action=AuditAction.OTHER,
                    target_obj=txn,
                    description="Poll task dispatched",
                    metadata={"gateway": gateway, "provider_id": provider_id, "external_ref": external_ref},
                )
            except Exception as enqueue_err:
                tb = traceback.format_exc()
                logger.exception(f"[{task_name}] failed to enqueue poll for txn {txn.id}: {enqueue_err}")
                cache.delete(claim_key)
                DeadLetterService().push(
                    task_name=task_name,
                    task_id=task_id,
                    payload={"txn_id": str(txn.id)},
                    error=str(enqueue_err),
                    traceback=tb,
                )
                skipped += 1

        logger.info(f"[{task_name}] finished. processed={processed}, skipped={skipped}, total={total}")
        return {"status": "OK", "processed": processed, "skipped": skipped, "available": total}

    except Exception as exc:
        tb = traceback.format_exc()
        logger.exception(f"[{task_name}] fatal error: {exc}")
        try:
            retries = getattr(self.request, "retries", 0)
            countdown = _compute_backoff(retries)
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            DeadLetterService().push(task_name=task_name, task_id=task_id, payload={}, error=str(exc), traceback=tb)
            return {"status": "FAILED", "error": str(exc)}