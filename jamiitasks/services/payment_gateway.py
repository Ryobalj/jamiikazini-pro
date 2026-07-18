# jamiitasks/services/payment_gateway.py

import uuid
import random
import logging
from django.core.exceptions import ValidationError
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.services.transaction_engine import TransactionEngine

logger = logging.getLogger(__name__)


def generate_reference():
    return uuid.uuid4().hex.upper()


def base_metadata(**extra):
    md = {"source_txn_id": generate_reference()}
    md.update(extra)
    return md


def send_to_gateway(account, amount):
    logger.info(f"Sending to gateway: account={account}, amount={amount}")
    try:
        if random.random() < 0.9:  # 90% success rate
            return True
        return False
    except Exception as e:
        logger.exception(f"send_to_gateway failed: {e}")
        return False


def validate_amount(amount):
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")


def initiate_topup(user, amount):
    validate_amount(amount)
    wallet = Wallet.objects.get(user=user)

    txn = TransactionEngine.initiate(
        wallet=wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.TOP_UP,
        initiated_by=user,
        metadata=base_metadata(),
    )
    logger.info(f"Topup initiated: user={user.id}, amount={amount}, txn_ref={txn.reference}")
    return txn


def initiate_withdrawal(user, amount, channel="MPESA"):
    validate_amount(amount)
    wallet = Wallet.objects.get(user=user)

    if wallet.available_balance < amount:
        raise ValidationError("Insufficient balance")

    txn = TransactionEngine.initiate(
        wallet=wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.WITHDRAWAL,
        initiated_by=user,
        metadata=base_metadata(channel=channel),
    )

    try:
        success = send_to_gateway(account=user.phone_number, amount=amount)
    except Exception as e:
        logger.exception("Withdrawal gateway exception")
        txn.mark_failed()
        raise

    if success:
        TransactionEngine.process(txn)
        logger.info(f"Withdrawal completed: user={user.id}, amount={amount}, txn_ref={txn.reference}")
    else:
        txn.mark_failed()
        logger.warning(f"Withdrawal failed: user={user.id}, txn_ref={txn.reference}")

    return txn


def transfer_funds(from_user, to_user, amount):
    validate_amount(amount)

    from_wallet = Wallet.objects.get(user=from_user)
    to_wallet = Wallet.objects.get(user=to_user)

    if from_wallet.available_balance < amount:
        raise ValidationError("Insufficient funds")

    txn = TransactionEngine.initiate(
        wallet=from_wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.TRANSFER,
        initiated_by=from_user,
        counterparty=to_user,
        metadata=base_metadata(recipient_id=str(to_user.id)),
    )

    TransactionEngine.process(txn)
    txn.refresh_from_db()

    # Double-entry: mirror record on the recipient side
    in_txn = Transaction.objects.create(
        initiated_by=to_user,
        wallet=to_wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.TRANSFER,
        status=txn.status,
        counterparty=from_user,
        metadata=base_metadata(mirror_of=str(txn.id)),
    )

    logger.info(f"Transfer completed: from_user={from_user.id}, to_user={to_user.id}, amount={amount}")
    return txn, in_txn


def make_payment(user, business_wallet, amount):
    validate_amount(amount)
    wallet = Wallet.objects.get(user=user)

    if wallet.available_balance < amount:
        raise ValidationError("Insufficient funds")

    txn = TransactionEngine.initiate(
        wallet=wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.PAYMENT,
        initiated_by=user,
        counterparty=business_wallet.user,
        metadata=base_metadata(merchant_id=str(business_wallet.user.id)),
    )

    TransactionEngine.process(txn)

    logger.info(f"Payment completed: user={user.id} paid {amount} to business {business_wallet.user.id}")
    return txn


def initiate_refund(original_txn: Transaction):
    if original_txn.status != Transaction.TransactionStatus.COMPLETED:
        raise ValidationError("Only completed transactions can be refunded.")

    if not original_txn.counterparty:
        raise ValidationError("No counterparty found for refund.")

    payer_wallet = Wallet.objects.get(user=original_txn.initiated_by)

    txn = TransactionEngine.initiate(
        wallet=payer_wallet,
        amount=original_txn.amount,
        transaction_type=Transaction.TransactionType.REFUND,
        initiated_by=original_txn.initiated_by,
        counterparty=original_txn.counterparty,
        metadata=base_metadata(reversed_transaction=str(original_txn.id), source_txn_id=str(original_txn.id)),
    )

    TransactionEngine.process(txn)

    logger.info(f"Refund processed: original_txn_ref={original_txn.reference}, refund_txn_ref={txn.reference}")
    return txn