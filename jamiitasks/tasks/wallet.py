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


# ============================================================
# WITHDRAWAL (payout) — punguza salio (hold) + PawaPay payout
# ============================================================
_PAWAPAY_PAYOUT_ACCEPTED = {"ACCEPTED", "SUBMITTED", "ENQUEUED", "PENDING", "PROCESSING"}


def debit_wallet_for_withdrawal(withdrawal) -> Transaction:
    """
    Punguza salio la wallet (hold) kwa ATOMIC + IDEMPOTENT. Hurudisha Transaction ya
    WITHDRAWAL. Hutupa ValueError kama salio halitoshi.
    """
    idempotency_key = f"withdrawal:{withdrawal.reference}"
    with db_transaction.atomic():
        existing = Transaction.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing

        wallet = Wallet.objects.select_for_update().get(user=withdrawal.user)
        if wallet.available_balance < Decimal(withdrawal.amount):
            raise ValueError("Insufficient balance")
        wallet.balance -= Decimal(withdrawal.amount)
        wallet.save(update_fields=["balance"])

        metadata = withdrawal.metadata if isinstance(withdrawal.metadata, dict) else {}
        txn = Transaction.objects.create(
            wallet=wallet,
            initiated_by=withdrawal.user,
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            status=Transaction.TransactionStatus.COMPLETED,
            amount=withdrawal.amount,
            reference=withdrawal.reference,
            receipt=metadata,
            idempotency_key=idempotency_key,
        )
        withdrawal.transaction = txn
        withdrawal.save(update_fields=["transaction"])
        return txn


def reverse_withdrawal(withdrawal) -> None:
    """
    Rejesha salio (re-credit) kwa withdrawal iliyoshindwa. IDEMPOTENT + ATOMIC —
    haitarejesha mara mbili, na inaweka status = REVERSED.
    """
    from jamiiwallet.models.withdrawal import Withdrawal
    reverse_key = f"withdrawal-reverse:{withdrawal.reference}"
    with db_transaction.atomic():
        w = Withdrawal.objects.select_for_update().get(pk=withdrawal.pk)
        if w.status == Withdrawal.WithdrawalStatus.REVERSED:
            return
        debit_exists = Transaction.objects.filter(idempotency_key=f"withdrawal:{w.reference}").exists()
        reverse_exists = Transaction.objects.filter(idempotency_key=reverse_key).exists()
        if debit_exists and not reverse_exists:
            wallet = Wallet.objects.select_for_update().get(user=w.user)
            wallet.balance += Decimal(w.amount)
            wallet.save(update_fields=["balance"])
            Transaction.objects.create(
                wallet=wallet,
                initiated_by=w.user,
                transaction_type=Transaction.TransactionType.REFUND,
                status=Transaction.TransactionStatus.COMPLETED,
                amount=w.amount,
                reference=f"REV-{w.reference}",
                receipt={"reversed_withdrawal": w.reference},
                idempotency_key=reverse_key,
            )
        w.status = Withdrawal.WithdrawalStatus.REVERSED
        w.save(update_fields=["status"])


# ============================================================
# TRANSFER (P2P, ndani ya mfumo) — hakuna gateway ya nje, synchronous
# ============================================================

def execute_transfer(transfer) -> None:
    """
    Hamisha salio kutoka wallet ya sender kwenda wallet ya recipient. ATOMIC +
    IDEMPOTENT (idempotency_key ya kipekee kwa reference). Hulinda dhidi ya
    deadlock kwa ku-lock wallet zote mbili kwa mpangilio thabiti (kwa wallet id,
    si kwa sender/recipient) - hii ni muhimu kwani A->B na B->A zinaweza kutokea
    kwa wakati mmoja.
    """
    idempotency_key = f"transfer:{transfer.reference}"
    with db_transaction.atomic():
        if Transaction.objects.filter(idempotency_key=idempotency_key).exists():
            return

        wallets = list(
            Wallet.objects.select_for_update()
            .filter(user_id__in=[transfer.sender_id, transfer.recipient_id])
            .order_by("id")
        )
        wallets_by_user = {w.user_id: w for w in wallets}
        sender_wallet = wallets_by_user.get(transfer.sender_id)
        recipient_wallet = wallets_by_user.get(transfer.recipient_id)

        if not sender_wallet or not recipient_wallet:
            transfer.mark_failed("Wallet haijapatikana kwa mtumaji au mpokeaji.")
            return

        if sender_wallet.available_balance < Decimal(transfer.amount):
            transfer.mark_failed("Salio halitoshi.")
            return

        sender_wallet.balance -= Decimal(transfer.amount)
        recipient_wallet.balance += Decimal(transfer.amount)
        sender_wallet.save(update_fields=["balance"])
        recipient_wallet.save(update_fields=["balance"])

        sender_txn = Transaction.objects.create(
            wallet=sender_wallet,
            initiated_by=transfer.sender,
            counterparty=transfer.recipient,
            transaction_type=Transaction.TransactionType.TRANSFER,
            status=Transaction.TransactionStatus.COMPLETED,
            amount=transfer.amount,
            reference=f"{transfer.reference}-OUT",
            metadata={"note": transfer.note, "direction": "sent"},
            idempotency_key=idempotency_key,
        )
        recipient_txn = Transaction.objects.create(
            wallet=recipient_wallet,
            initiated_by=transfer.sender,
            counterparty=transfer.sender,
            transaction_type=Transaction.TransactionType.TRANSFER,
            status=Transaction.TransactionStatus.COMPLETED,
            amount=transfer.amount,
            reference=f"{transfer.reference}-IN",
            metadata={"note": transfer.note, "direction": "received"},
            idempotency_key=f"{idempotency_key}:in",
        )
        transfer.mark_completed(sender_txn, recipient_txn)
        logger.info(
            "Transfer completed ref=%s sender=%s recipient=%s amount=%s",
            transfer.reference, transfer.sender_id, transfer.recipient_id, transfer.amount,
        )


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def process_transfer_transaction(self, transfer_id):
    """Celery task inayotekeleza Transfer. Ni synchronous kimantiki (hakuna gateway
    ya nje ya kusubiri) - hufanya kazi kwa uhakika hata EAGER mode."""
    from jamiiwallet.models.transfer import Transfer
    start_time = time.time()
    task_name = "process_transfer_transaction"
    task_id = str(self.request.id)

    try:
        transfer = Transfer.objects.select_related("sender", "recipient").get(id=transfer_id)
    except Transfer.DoesNotExist:
        _log_task(task_name, task_id, "FAILED", f"Transfer {transfer_id} not found", start_time)
        return f"Transfer {transfer_id} not found."

    if transfer.status != Transfer.TransferStatus.INITIATED:
        msg = f"Transfer {transfer.reference} already processed (status={transfer.status})."
        _log_task(task_name, task_id, "SKIPPED", msg, start_time)
        return msg

    try:
        execute_transfer(transfer)
        msg = f"Transfer {transfer.reference} processed (status={transfer.status})."
        _log_task(task_name, task_id, "SUCCESS", msg, start_time)
        logger.info(msg)
        return msg
    except Exception as e:
        err_msg = f"Error processing Transfer {transfer.reference}: {str(e)}"
        logger.error(err_msg, exc_info=True)
        _log_task(task_name, task_id, "FAILED", err_msg, start_time)
        raise self.retry(exc=e, countdown=10)


def initiate_pawapay_payout(withdrawal) -> dict:
    """Anzisha PawaPay payout kwenda simu ya mteja. Huhifadhi payoutId + status + kosa."""
    import requests
    gw = PawaPayGateway()
    md = withdrawal.metadata if isinstance(withdrawal.metadata, dict) else {}
    try:
        resp = gw.initiate_payout(
            amount=str(withdrawal.amount),
            currency=getattr(settings, "PAWAPAY_DEFAULT_CURRENCY", "TZS"),
            phone=withdrawal.phone,
            provider=withdrawal.provider,
            client_reference_id=withdrawal.reference,
            metadata={"withdrawal_id": str(withdrawal.id), "user_id": str(withdrawal.user_id)},
        )
    except requests.exceptions.HTTPError as e:
        reason = {}
        try:
            reason = e.response.json()
        except Exception:
            reason = {"error": str(e)}
        md["provider_error"] = reason
        withdrawal.metadata = md
        withdrawal.save(update_fields=["metadata"])
        logger.error("PawaPay payout REJECTED (HTTP) ref=%s reason=%s", withdrawal.reference, reason)
        return {"status": "REJECTED", "error": reason}

    status = str(resp.get("status") or "").upper()
    md["payoutId"] = resp.get("payoutId")
    md["provider_status"] = status
    md["provider_response"] = resp
    withdrawal.metadata = md
    withdrawal.save(update_fields=["metadata"])
    logger.info("PawaPay payout ref=%s status=%s payoutId=%s", withdrawal.reference, status, resp.get("payoutId"))
    return resp


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_withdrawal_transaction(self, withdrawal_id):
    """
    Debit wallet (hold) -> anzisha PawaPay payout. Ikishindwa KUANZISHA, rejesha salio.
    Uthibitisho wa mwisho (COMPLETED/FAILED) hufanywa na webhook.
    """
    from jamiiwallet.models.withdrawal import Withdrawal
    start_time = time.time()
    task_name = "process_withdrawal_transaction"
    task_id = str(self.request.id)

    try:
        withdrawal = Withdrawal.objects.select_related("user").get(id=withdrawal_id)
    except Withdrawal.DoesNotExist:
        _log_task(task_name, task_id, "FAILED", f"Withdrawal {withdrawal_id} not found", start_time)
        return f"Withdrawal {withdrawal_id} not found."

    if withdrawal.status != Withdrawal.WithdrawalStatus.INITIATED:
        msg = f"Withdrawal {withdrawal.reference} already processed (status={withdrawal.status})."
        _log_task(task_name, task_id, "SKIPPED", msg, start_time)
        return msg

    # 1) Debit (hold) salio
    try:
        debit_wallet_for_withdrawal(withdrawal)
    except ValueError:
        withdrawal.mark_failed()
        msg = f"Withdrawal {withdrawal.reference} failed: insufficient balance."
        _log_task(task_name, task_id, "FAILED", msg, start_time)
        logger.warning(msg)
        return msg

    # 2) Anzisha payout
    resp = initiate_pawapay_payout(withdrawal)
    status = str(resp.get("status") or "").upper()
    if status in _PAWAPAY_PAYOUT_ACCEPTED:
        withdrawal.mark_processing()
        msg = f"Withdrawal {withdrawal.reference}: PawaPay payout initiated (awaiting callback)."
        _log_task(task_name, task_id, "SUCCESS", msg, start_time)
        logger.info(msg)
        return msg

    # 3) Kushindwa kuanzisha -> REJESHA salio
    reverse_withdrawal(withdrawal)
    msg = f"Withdrawal {withdrawal.reference} payout NOT accepted (status={status}) -> salio limerejeshwa."
    _log_task(task_name, task_id, "FAILED", msg, start_time)
    logger.error(msg)
    return msg