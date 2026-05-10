# jamiitasks/tasks/wallet.py

import logging
import time
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from celery import shared_task

from jamiiwallet.models.topup import TopUp
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.wallet import Wallet
from jamiitasks.models import TaskLog
from jamiitasks.utils.throttling import throttled_task

# Import your gateways
from payments.gateways.flutterwave.client import FlutterwaveGateway
from payments.gateways.pawapay.client import PawaPayGateway
from payments.gateways.stripe.client import StripeGateway

logger = logging.getLogger(__name__)

# ---- Gateway confirmation helper
def confirm_with_gateway(topup: TopUp) -> bool:
    """
    Checks payment status of a TopUp across registered gateways.
    Returns True if payment is confirmed, False otherwise.
    """
    channel = (topup.channel or "").lower()
    try:
        if channel in ["flutterwave", "fw"]:
            gw = FlutterwaveGateway()
        elif channel in ["pawapay", "pp"]:
            gw = PawaPayGateway()
        elif channel in ["stripe", "st"]:
            gw = StripeGateway()
        else:
            logger.warning(f"Unknown payment channel '{topup.channel}' for topup {topup.reference}")
            return False

        # Each gateway should have a check_transaction_status method returning dict with "status"
        result = gw.check_transaction_status(topup.reference)
        status = str(result.get("status") or "").upper()
        return status == "SUCCESS"

    except Exception as e:
        logger.exception(f"Error confirming topup {topup.reference} via {channel}: {e}")
        return False


# ---- Celery task
@shared_task(
    bind=True,
    max_retries=4,
    default_retry_delay=30,
    rate_limit="25/m",
)
@throttled_task(rate_limit="1/m", redis_key="wallet:confirm_topup_transaction")
def confirm_topup_transaction(self, topup_id):
    """
    Confirms a wallet top-up and updates the user's balance atomically.
    - Retries automatically with exponential backoff.
    - Throttled via redis_key per topup (1/minute).
    - Logged in TaskLog table.
    - Enforces idempotency via Transaction.idempotency_key.
    """
    start_time = time.time()
    task_name = "confirm_topup_transaction"
    task_id = str(self.request.id)

    try:
        topup = TopUp.objects.select_related("user").get(id=topup_id)
    except TopUp.DoesNotExist:
        _log_task(task_name, task_id, "FAILED", f"TopUp {topup_id} not found", start_time)
        return f"TopUp with ID {topup_id} not found."

    if topup.status in [TopUp.TopUpStatus.CONFIRMED, TopUp.TopUpStatus.FAILED]:
        msg = f"TopUp {topup.reference} already processed (status={topup.status})."
        logger.info(msg)
        _log_task(task_name, task_id, "SKIPPED", msg, start_time)
        return msg

    # 🔐 Generate idempotency key unique per TopUp reference
    idempotency_key = f"topup:{topup.reference}"

    try:
        # ✅ Confirm payment via gateway
        payment_confirmed = confirm_with_gateway(topup)

        if not payment_confirmed:
            topup.mark_failed()
            msg = f"TopUp {topup.reference} failed to confirm."
            _log_task(task_name, task_id, "FAILED", msg, start_time)
            logger.warning(msg)
            return msg

        with db_transaction.atomic():
            # 🧩 Idempotency: check if transaction already exists
            existing_txn = Transaction.objects.filter(idempotency_key=idempotency_key).first()
            if existing_txn:
                msg = f"[Idempotent Skip] Transaction already exists for {topup.reference}."
                logger.info(msg)
                _log_task(task_name, task_id, "SKIPPED", msg, start_time)
                # Ensure TopUp is marked confirmed
                if topup.status != TopUp.TopUpStatus.CONFIRMED:
                    topup.mark_confirmed(existing_txn)
                return msg

            # 💰 Credit wallet balance atomically
            wallet = Wallet.objects.select_for_update().get(user=topup.user)
            wallet.balance += Decimal(topup.amount)
            wallet.save(update_fields=["balance"])

            metadata = topup.metadata if isinstance(topup.metadata, dict) else {}

            # 🧾 Create Transaction with idempotency key
            txn = Transaction.objects.create(
                wallet=wallet,
                initiated_by=topup.user,
                transaction_type=Transaction.TransactionType.TOP_UP,
                status=Transaction.TransactionStatus.COMPLETED,
                amount=topup.amount,
                reference=topup.reference,
                receipt=metadata,
                idempotency_key=idempotency_key,
            )

            # ✅ Mark top-up as confirmed
            topup.mark_confirmed(txn)

        msg = f"TopUp {topup.reference} confirmed successfully."
        logger.info(msg)
        _log_task(task_name, task_id, "SUCCESS", msg, start_time)
        return msg

    except Exception as e:
        # ⏳ Exponential backoff for retries
        wait_time = 10 * (2 ** self.request.retries)
        err_msg = f"Error processing TopUp {topup.reference}: {str(e)}"
        logger.error(err_msg, exc_info=True)
        _log_task(task_name, task_id, "FAILED", err_msg, start_time)
        raise self.retry(exc=e, countdown=wait_time)


# ---- TaskLog helper
def _log_task(task_name: str, task_id: str, status: str, message: str, start_time: float):
    """
    Records each task execution in TaskLog for observability.
    """
    duration_ms = int((time.time() - start_time) * 1000)
    try:
        TaskLog.record(
            task_name=task_name,
            task_id=task_id,
            status=status,
            details=message,
            duration_ms=duration_ms,
        )
    except Exception as e:
        logger.warning(f"[TaskLog] Failed to record {task_name}: {e}")