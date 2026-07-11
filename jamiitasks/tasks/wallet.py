# jamiitasks/tasks/wallet.py

import logging
import time
from decimal import Decimal
from django.conf import settings
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


# ---- Wallet crediting (idempotent + atomic) — reused by webhook & reconciliation
def credit_wallet_for_topup(topup: TopUp) -> Transaction:
    """
    Ongeza salio la wallet kwa TopUp iliyofaulu. IDEMPOTENT (idempotency_key ya kipekee
    kwa reference) na ATOMIC (select_for_update). Hurudisha Transaction. Salama kuitwa
    mara nyingi (webhook + reconciliation) bila kuongeza mara mbili.
    """
    idempotency_key = f"topup:{topup.reference}"
    with db_transaction.atomic():
        existing_txn = Transaction.objects.filter(idempotency_key=idempotency_key).first()
        if existing_txn:
            if topup.status != TopUp.TopUpStatus.CONFIRMED:
                topup.mark_confirmed(existing_txn)
            return existing_txn

        wallet = Wallet.objects.select_for_update().get(user=topup.user)
        wallet.balance += Decimal(topup.amount)
        wallet.save(update_fields=["balance"])

        metadata = topup.metadata if isinstance(topup.metadata, dict) else {}
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
        topup.mark_confirmed(txn)
        return txn


# PawaPay initiate-deposit statuses zinazomaanisha ombi limekubaliwa (STK push imetumwa)
_PAWAPAY_ACCEPTED = {"ACCEPTED", "SUBMITTED", "ENQUEUED", "PENDING", "PROCESSING"}


# ---- PawaPay deposit initiation (STK push)
def initiate_pawapay_deposit(topup: TopUp) -> dict:
    """
    Anzisha deposit ya PawaPay (STK push kwa simu ya mlipaji). Huhifadhi depositId +
    status + sababu ya kosa (kama ipo) kwenye metadata, na huandika logs za wazi.
    Salio LA WALLET HALIONGEZWI hapa — huongezwa na webhook baada ya callback ya SUCCESS.
    """
    import requests

    gw = PawaPayGateway()
    md = topup.metadata if isinstance(topup.metadata, dict) else {}

    try:
        resp = gw.initiate_deposit(
            amount=str(topup.amount),
            currency=getattr(settings, "PAWAPAY_DEFAULT_CURRENCY", "TZS"),
            phone=topup.phone,
            provider=topup.provider,
            client_reference_id=topup.reference,
            metadata={"topup_id": str(topup.id), "user_id": str(topup.user_id)},
        )
    except requests.exceptions.HTTPError as e:
        # PawaPay imekataa ombi (4xx) — kamata sababu, failisha topup (USIRUDIE)
        reason = {}
        try:
            reason = e.response.json()
        except Exception:
            reason = {"error": str(e)}
        md["provider_error"] = reason
        topup.metadata = md
        topup.save(update_fields=["metadata"])
        topup.mark_failed()
        logger.error(
            "PawaPay deposit REJECTED (HTTP) ref=%s provider=%s phone=%s amount=%s reason=%s",
            topup.reference, topup.provider, topup.phone, topup.amount, reason,
        )
        return {"status": "REJECTED", "error": reason}

    status = str(resp.get("status") or "").upper()
    md["depositId"] = resp.get("depositId")
    md["provider_status"] = status
    md["provider_response"] = resp
    topup.metadata = md

    if status in _PAWAPAY_ACCEPTED:
        topup.status = TopUp.TopUpStatus.PROCESSING
        topup.save(update_fields=["metadata", "status"])
        logger.info(
            "PawaPay deposit ACCEPTED ref=%s status=%s depositId=%s (STK push imetumwa kwa %s)",
            topup.reference, status, resp.get("depositId"), topup.phone,
        )
    else:
        # REJECTED / DUPLICATE_IGNORED / FAILED — soft-reject ndani ya 200
        topup.save(update_fields=["metadata"])
        topup.mark_failed()
        logger.error(
            "PawaPay deposit NOT accepted ref=%s status=%s provider=%s phone=%s resp=%s",
            topup.reference, status, topup.provider, topup.phone, resp,
        )
    return resp


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

    channel = (topup.channel or "").lower()

    try:
        # ---- PawaPay: mobile-money STK-push flow ----
        if channel in ("pawapay", "pp"):
            if topup.status == TopUp.TopUpStatus.INITIATED:
                # Anzisha STK push. Salio la wallet huongezwa na WEBHOOK baada ya
                # callback ya SUCCESS (si hapa) — kwa hivyo hatuongezi salio sasa.
                initiate_pawapay_deposit(topup)
                msg = f"TopUp {topup.reference}: PawaPay deposit initiated (awaiting callback)."
                _log_task(task_name, task_id, "SUCCESS", msg, start_time)
                logger.info(msg)
                return msg

            # Status PROCESSING -> reconciliation: hakiki status kwa PawaPay
            if confirm_with_gateway(topup):
                credit_wallet_for_topup(topup)
                msg = f"TopUp {topup.reference} confirmed (reconciliation)."
                _log_task(task_name, task_id, "SUCCESS", msg, start_time)
                logger.info(msg)
                return msg
            msg = f"TopUp {topup.reference} bado inasubiri uthibitisho (hakuna SUCCESS bado)."
            _log_task(task_name, task_id, "PENDING", msg, start_time)
            return msg

        # ---- Hosted gateways (Flutterwave / Stripe): poll status then credit ----
        if not confirm_with_gateway(topup):
            topup.mark_failed()
            msg = f"TopUp {topup.reference} failed to confirm."
            _log_task(task_name, task_id, "FAILED", msg, start_time)
            logger.warning(msg)
            return msg

        credit_wallet_for_topup(topup)
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