# payments/wallet_bridge.py

from decimal import Decimal
from django.core.exceptions import ValidationError
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.services.transaction_engine import TransactionEngine
from jamiiwallet.models.transaction import Transaction

class WalletBridge:
    """
    Bridge layer ya payments kuwasiliana na jamiiwallet transaction engine.
    """

    @staticmethod
    def top_up_wallet(user, amount: Decimal) -> Transaction:
        wallet = Wallet.objects.get(user=user)
        # Initiate top-up transaction
        transaction = TransactionEngine.initiate(
            wallet=wallet,
            amount=amount,
            transaction_type=Transaction.TransactionType.TOP_UP,
            initiated_by=user,
        )
        # Process immediately or defer with Celery
        return TransactionEngine.process(transaction)

    @staticmethod
    def withdraw_from_wallet(user, amount: Decimal) -> Transaction:
        wallet = Wallet.objects.get(user=user)
        transaction = TransactionEngine.initiate(
            wallet=wallet,
            amount=amount,
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            initiated_by=user,
        )
        return TransactionEngine.process(transaction)

    @staticmethod
    def transfer_between_wallets(sender, recipient_wallet_id, amount: Decimal) -> Transaction:
        sender_wallet = Wallet.objects.get(user=sender)
        recipient_wallet = Wallet.objects.get(id=recipient_wallet_id)
        transaction = TransactionEngine.initiate(
            wallet=sender_wallet,
            amount=amount,
            transaction_type=Transaction.TransactionType.TRANSFER,
            initiated_by=sender,
            counterparty=recipient_wallet,
        )
        return TransactionEngine.process(transaction)