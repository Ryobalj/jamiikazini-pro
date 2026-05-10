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
    )
    logger.info(f"Topup initiated: user={user.id}, amount={amount}, txn_ref={txn.reference}")
    return txn


def initiate_withdrawal(user, amount, channel="MPESA"):
    validate_amount(amount)
    wallet = Wallet.objects.get(user=user)

    if wallet.balance < amount:
        raise ValidationError("Insufficient balance")

    txn = TransactionEngine.initiate(
        wallet=wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.WITHDRAWAL,
        initiated_by=user,
        metadata={"channel": channel},
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

    if from_wallet.balance < amount:
        raise ValidationError("Insufficient funds")

    txn = TransactionEngine.initiate(
        wallet=from_wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.TRANSFER,
        initiated_by=from_user,
        counterparty=to_user,
    )

    TransactionEngine.process(txn)

    logger.info(f"Transfer completed: from_user={from_user.id}, to_user={to_user.id}, amount={amount}")
    return txn


def make_payment(user, business_wallet, amount):
    validate_amount(amount)
    wallet = Wallet.objects.get(user=user)

    if wallet.balance < amount:
        raise ValidationError("Insufficient funds")

    txn = TransactionEngine.initiate(
        wallet=wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.PAYMENT,
        initiated_by=user,
        counterparty=business_wallet.user,
    )

    TransactionEngine.process(txn)

    logger.info(f"Payment completed: user={user.id} paid {amount} to business {business_wallet.user.id}")
    return txn


def initiate_refund(original_txn: Transaction):
    if original_txn.status != Transaction.TransactionStatus.COMPLETED:
        raise ValidationError("Only completed transactions can be refunded.")

    if not original_txn.counterparty:
        raise ValidationError("No counterparty found for refund.")

    refund_wallet = Wallet.objects.get(user=original_txn.counterparty)

    txn = TransactionEngine.initiate(
        wallet=refund_wallet,
        amount=original_txn.amount,
        transaction_type=Transaction.TransactionType.REFUND,
        initiated_by=original_txn.counterparty,
        counterparty=original_txn.initiated_by,
        metadata={"reversed_transaction": original_txn.id},
    )

    TransactionEngine.process(txn)

    logger.info(f"Refund processed: original_txn_ref={original_txn.reference}, refund_txn_ref={txn.reference}")
    return txn