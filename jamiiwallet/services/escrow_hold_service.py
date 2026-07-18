# jamiiwallet/services/escrow_hold_service.py
#
# Wrapper nyembamba juu ya TransactionEngine kwa ajili ya HOLD zenye malipo ya
# awamu (milestone) au sehemu (partial) - haigusi TransactionEngine._hold/
# _capture/_void wala escrow ya delivery iliyopo (logistics/services/
# escrow_release.py), ambayo inaendelea kuita TransactionEngine moja kwa moja.
#
# Utaratibu wa kufunga (lock ordering): EscrowHold inafungwa (select_for_update)
# KABLA ya TransactionEngine.process() kufunga Wallet - kamwe kinyume chake -
# ili kuepuka deadlock na njia nyingine zozote za code zinazoweza kufunga
# Wallet kisha EscrowHold baadaye.

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction

from jamiiwallet.models.escrow_hold import EscrowHold, EscrowHoldStatus
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.services.transaction_engine import TransactionEngine


@db_transaction.atomic
def open_hold(wallet, amount, initiated_by, linked_object=None, idempotency_key=None, metadata=None) -> EscrowHold:
    """Anzisha HOLD mpya na uifunge kwenye EscrowHold ya itemized."""
    if amount <= 0:
        raise ValidationError("Kiasi cha kushikilia lazima kiwe zaidi ya sifuri.")

    txn = TransactionEngine.initiate(
        wallet=wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.HOLD,
        initiated_by=initiated_by,
        metadata=metadata,
        idempotency_key=idempotency_key,
    )
    if txn.status == Transaction.TransactionStatus.PENDING:
        TransactionEngine.process(txn)

    # Idempotent retry: EscrowHold inaweza kuwa tayari ipo kwa HOLD hii.
    existing = EscrowHold.objects.filter(hold_transaction=txn).first()
    if existing:
        return existing

    content_type = None
    object_id = None
    if linked_object is not None:
        content_type = ContentType.objects.get_for_model(linked_object)
        object_id = str(linked_object.pk)

    return EscrowHold.objects.create(
        hold_transaction=txn,
        wallet=wallet,
        total_held=amount,
        content_type=content_type,
        object_id=object_id,
    )


@db_transaction.atomic
def capture_from_hold(escrow_hold, amount, counterparty, initiated_by, idempotency_key=None, metadata=None) -> Transaction:
    """Toa kiasi (amount) kutoka kwenye EscrowHold kwenda kwa counterparty - haiwezi kuzidi remaining."""
    if amount <= 0:
        raise ValidationError("Kiasi cha capture lazima kiwe zaidi ya sifuri.")

    eh = EscrowHold.objects.select_for_update().get(pk=escrow_hold.pk)
    if eh.status != EscrowHoldStatus.OPEN:
        raise ValidationError("Escrow hold hii tayari imefungwa.")
    if amount > eh.remaining:
        raise ValidationError("Kiasi kinachoombwa kinazidi kilichobaki kwenye hold hii.")

    txn = TransactionEngine.initiate(
        wallet=eh.wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.CAPTURE,
        initiated_by=initiated_by,
        counterparty=counterparty,
        metadata=metadata,
        idempotency_key=idempotency_key,
    )
    if txn.status == Transaction.TransactionStatus.PENDING:
        TransactionEngine.process(txn)
        eh.total_captured += amount
        if eh.remaining <= 0:
            eh.status = EscrowHoldStatus.CLOSED
        eh.save(update_fields=["total_captured", "status", "updated_at"])
    # idempotent replay (txn already existed/processed) - haihitaji kuongeza tena.

    return txn


@db_transaction.atomic
def void_remaining(escrow_hold, initiated_by, idempotency_key=None, metadata=None) -> Transaction | None:
    """Achilia kilichobaki (remaining) cha EscrowHold kwa mmiliki wa wallet, kisha ifunge."""
    eh = EscrowHold.objects.select_for_update().get(pk=escrow_hold.pk)
    if eh.status != EscrowHoldStatus.OPEN:
        return None

    remaining = eh.remaining
    if remaining <= 0:
        eh.status = EscrowHoldStatus.CLOSED
        eh.save(update_fields=["status", "updated_at"])
        return None

    txn = TransactionEngine.initiate(
        wallet=eh.wallet,
        amount=remaining,
        transaction_type=Transaction.TransactionType.VOID,
        initiated_by=initiated_by,
        metadata=metadata,
        idempotency_key=idempotency_key,
    )
    if txn.status == Transaction.TransactionStatus.PENDING:
        TransactionEngine.process(txn)
        eh.total_voided += remaining

    eh.status = EscrowHoldStatus.CLOSED
    eh.save(update_fields=["total_voided", "status", "updated_at"])
    return txn
