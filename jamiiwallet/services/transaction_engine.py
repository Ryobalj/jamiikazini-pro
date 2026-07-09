# jamiiwallet/services/transaction_engine.py

from decimal import Decimal, ROUND_DOWN
from contextlib import nullcontext
from django.db import transaction as db_transaction
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
import logging

from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.wallet import Wallet
from payments.models.audit_log import AuditLog, AuditAction

# ðŸ”¹ Pre-processing imports
from jamiiwallet.services.transaction_preprocessor import (
    sync_pre_process_transaction,
    async_pre_process_transaction,
)

# ðŸ”¹ Cache layer imports
from jamiiwallet.services.cache_utils import (
    get_cached_balance,
    set_cached_balance,
    invalidate_cached_balance,
    acquire_balance_lock,
)

logger = logging.getLogger(__name__)


class TransactionEngine:
    """
    Engine kuu ya kushughulikia transactions za jamiiwallet.
    Inajumuisha:
      - Top ups
      - Withdrawals
      - Transfers
      - Payments
      - Refunds
    """

    # -----------------------------------------------------------------------------------
    @staticmethod
    @db_transaction.atomic
    def process(transaction: Transaction) -> Transaction:
        """
        Shughulikia transaction ikiwa bado ipo PENDING, kwa kufanya mabadiliko ya salio la wallet
        kwa njia salama, na kuweka status kuwa COMPLETED au FAILED kulingana na matokeo.
        """
        if not transaction.pk:
            raise ValidationError("Transaction must be saved before processing.")

        if transaction.status != Transaction.TransactionStatus.PENDING:
            raise ValidationError("Transaction must be in pending state before processing.")

        try:
            match transaction.transaction_type:
                case Transaction.TransactionType.TOP_UP:
                    TransactionEngine._top_up(transaction)
                case Transaction.TransactionType.WITHDRAWAL:
                    TransactionEngine._withdraw(transaction)
                case Transaction.TransactionType.TRANSFER:
                    TransactionEngine._transfer(transaction)
                case Transaction.TransactionType.PAYMENT:
                    TransactionEngine._payment(transaction)
                case Transaction.TransactionType.REFUND:
                    TransactionEngine._refund(transaction)
                case _:
                    raise ValidationError("Unsupported transaction type.")

            # âœ… Ikiwa hakuna error â€” mark as completed
            transaction.status = Transaction.TransactionStatus.COMPLETED
            transaction.updated_at = timezone.now()
            transaction.save(update_fields=["status", "updated_at"])

            # ðŸ”¹ Audit log
            AuditLog.log_action(
                user=transaction.user,
                action=AuditAction.PAYMENT if transaction.transaction_type in [
                    Transaction.TransactionType.PAYMENT,
                    Transaction.TransactionType.TRANSFER
                ] else AuditAction.OTHER,
                target_obj=transaction,
                description=f"Transaction processed successfully: {transaction.amount} ({transaction.transaction_type})",
                metadata={
                    "wallet_id": str(transaction.user.id),
                    "txn_type": transaction.transaction_type,
                    "amount": float(transaction.amount),
                    "status": transaction.status,
                    **(transaction.metadata or {}),
                },
            )

            logger.info(f"âœ… Transaction processed successfully: id={transaction.id}")
            return transaction

        except Exception as e:
            transaction.status = Transaction.TransactionStatus.FAILED
            transaction.updated_at = timezone.now()
            transaction.receipt = {
                **(transaction.receipt or {}),
                "error": str(e),
                "failed_at": timezone.now().isoformat(),
            }
            transaction.save(update_fields=["status", "updated_at", "_receipt"])

            # ðŸ”¹ Audit log kwa failures
            AuditLog.log_action(
                user=transaction.user,
                action=AuditAction.PAYMENT_RETRY,
                target_obj=transaction,
                description=f"Transaction failed: {str(e)}",
                metadata={
                    "wallet_id": str(transaction.user.id),
                    "txn_type": transaction.transaction_type,
                    "amount": float(transaction.amount),
                    **(transaction.metadata or {}),
                },
            )

            logger.error(f"âŒ Transaction {transaction.id} failed: {e}", exc_info=True)
            raise

    # -----------------------------------------------------------------------------------
    @staticmethod
    def initiate(account_identifier, amount, txn_type, metadata=None) -> Transaction:
        """
        Anzisha transaction mpya ikiwa na hatua ya async/sync pre-processing na idempotency check.
        """
        logger.info(f"ðŸš€ Initiating transaction for {account_identifier} with {txn_type}")

        # 1ï¸âƒ£ Pre-processing (sync, kabla ya kuunda transaction)
        try:
            user, metadata = sync_pre_process_transaction(account_identifier, metadata)
            AuditLog.log_action(
                user=user,
                action=AuditAction.VALIDATION,
                target_obj=None,
                description="Pre-processing validation successful",
                metadata={"identifier": account_identifier, **(metadata or {})},
            )
            logger.info(f"âœ… Pre-processing passed for {account_identifier}")

        except ValidationError as ve:
            logger.warning(f"âš ï¸ Pre-processing failed for {account_identifier}: {ve}")
            AuditLog.log_action(
                user=None,
                action=AuditAction.VALIDATION,
                target_obj=None,
                description=f"Pre-processing failed: {ve}",
                metadata={"identifier": account_identifier, "error": str(ve)},
            )
            raise

        # 2ï¸âƒ£ Idempotency check
        ref_key = metadata.get("idempotency_key") if metadata else None
        if ref_key:
            existing = Transaction.objects.filter(
                user=user,
                metadata__idempotency_key=ref_key,
            ).first()
            if existing:
                logger.warning(f"âš ï¸ Duplicate idempotent transaction detected: {existing.id}")
                AuditLog.log_action(
                    user=user,
                    action=AuditAction.OTHER,
                    target_obj=existing,
                    description="Duplicate idempotent transaction detected",
                    metadata={"idempotency_key": ref_key},
                )
                return existing

        # 3ï¸âƒ£ Kuunda transaction
        txn = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type=txn_type,
            status=Transaction.TransactionStatus.PENDING,
            metadata=metadata or {},
        )

        # 4ï¸âƒ£ Audit log
        AuditLog.log_action(
            user=user,
            action=AuditAction.CREATE,
            target_obj=txn,
            description=f"Transaction initiated: {txn.amount} ({txn_type})",
            metadata={"idempotency_key": ref_key, **(metadata or {})},
        )

        logger.info(f"ðŸŸ¢ Transaction initiated: {txn.id}")

        # 5ï¸âƒ£ Trigger optional async preprocessor for background audit
        async_pre_process_transaction.delay(account_identifier, metadata)

        return txn

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _top_up(transaction: Transaction):
        wallet = Wallet.objects.select_for_update().get(user=transaction.user)

        # Debit the refunding party (merchant) first, then credit the payer.
        if transaction.counterparty_id:
            refunder_wallet = Wallet.objects.select_for_update().get(user_id=transaction.counterparty_id)
            with acquire_balance_lock(refunder_wallet.user.id) or nullcontext():
                if refunder_wallet.balance < transaction.amount:
                    raise ValidationError("Insufficient balance to issue refund.")
                invalidate_cached_balance(refunder_wallet.user.id)
                refunder_wallet.balance -= transaction.amount
                refunder_wallet.save(update_fields=["balance"])
                set_cached_balance(refunder_wallet.user.id, refunder_wallet.balance)

        with acquire_balance_lock(wallet.user.id) or nullcontext():
            invalidate_cached_balance(wallet.user.id)
            wallet.balance += transaction.amount
            wallet.save(update_fields=["balance"])
            set_cached_balance(wallet.user.id, wallet.balance)

        logger.debug(f"ðŸ’° Wallet top-up successful for {wallet.user}: +{transaction.amount}")

        AuditLog.log_action(
            user=transaction.user,
            action=AuditAction.UPDATE,
            target_obj=wallet,
            description=f"Top-up applied: +{transaction.amount}",
            metadata={"transaction_id": str(transaction.id), "new_balance": float(wallet.balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _withdraw(transaction: Transaction):
        wallet = Wallet.objects.select_for_update().get(user=transaction.user)

        with acquire_balance_lock(wallet.user.id) or nullcontext():
            if wallet.balance < transaction.amount:
                raise ValidationError("Insufficient balance for withdrawal.")
            invalidate_cached_balance(wallet.user.id)
            wallet.balance -= transaction.amount
            wallet.save(update_fields=["balance"])
            set_cached_balance(wallet.user.id, wallet.balance)

        logger.debug(f"ðŸ§ Wallet withdrawal successful for {wallet.user}: -{transaction.amount}")

        AuditLog.log_action(
            user=transaction.user,
            action=AuditAction.UPDATE,
            target_obj=wallet,
            description=f"Withdrawal applied: -{transaction.amount}",
            metadata={"transaction_id": str(transaction.id), "new_balance": float(wallet.balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _transfer(transaction: Transaction):
        metadata = transaction.metadata or {}
        recipient_id = metadata.get("recipient_id")
        if not recipient_id:
            raise ValidationError("Recipient ID required for transfer.")

        sender_wallet = Wallet.objects.select_for_update().get(user=transaction.user)
        recipient_wallet = Wallet.objects.select_for_update().get(user_id=recipient_id)

        with acquire_balance_lock(sender_wallet.user.id) or nullcontext():
            with acquire_balance_lock(recipient_wallet.user.id) or nullcontext():
                if sender_wallet.balance < transaction.amount:
                    raise ValidationError("Insufficient balance for transfer.")

                invalidate_cached_balance(sender_wallet.user.id)
                invalidate_cached_balance(recipient_wallet.user.id)

                sender_wallet.balance -= transaction.amount
                recipient_wallet.balance += transaction.amount

                sender_wallet.save(update_fields=["balance"])
                recipient_wallet.save(update_fields=["balance"])

                set_cached_balance(sender_wallet.user.id, sender_wallet.balance)
                set_cached_balance(recipient_wallet.user.id, recipient_wallet.balance)

        logger.debug(f"ðŸ” Transfer {transaction.amount} from {sender_wallet.user} to {recipient_wallet.user}")

        AuditLog.log_action(
            user=transaction.user,
            action=AuditAction.UPDATE,
            target_obj=sender_wallet,
            description=f"Transfer sent: -{transaction.amount} to {recipient_wallet.user}",
            metadata={"transaction_id": str(transaction.id), "recipient_id": recipient_id, "new_balance": float(sender_wallet.balance)},
        )
        AuditLog.log_action(
            user=transaction.user,
            action=AuditAction.UPDATE,
            target_obj=recipient_wallet,
            description=f"Transfer received: +{transaction.amount} from {sender_wallet.user}",
            metadata={"transaction_id": str(transaction.id), "sender_id": str(transaction.user.id), "new_balance": float(recipient_wallet.balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _payment(transaction: Transaction):
        metadata = transaction.metadata or {}
        merchant_id = metadata.get("merchant_id")
        if not merchant_id:
            raise ValidationError("Merchant ID required for payment.")

        payer_wallet = Wallet.objects.select_for_update().get(user=transaction.user)
        merchant_wallet = Wallet.objects.select_for_update().get(user_id=merchant_id)

        with acquire_balance_lock(payer_wallet.user.id) or nullcontext():
            with acquire_balance_lock(merchant_wallet.user.id) or nullcontext():
                if payer_wallet.balance < transaction.amount:
                    raise ValidationError("Insufficient balance for payment.")

                invalidate_cached_balance(payer_wallet.user.id)
                invalidate_cached_balance(merchant_wallet.user.id)

                payer_wallet.balance -= transaction.amount
                merchant_wallet.balance += transaction.amount

                payer_wallet.save(update_fields=["balance"])
                merchant_wallet.save(update_fields=["balance"])

                set_cached_balance(payer_wallet.user.id, payer_wallet.balance)
                set_cached_balance(merchant_wallet.user.id, merchant_wallet.balance)

        logger.debug(f"ðŸ’³ Payment {transaction.amount} from {payer_wallet.user} to merchant {merchant_wallet.user}")

        AuditLog.log_action(
            user=transaction.user,
            action=AuditAction.PAYMENT,
            target_obj=payer_wallet,
            description=f"Payment made: -{transaction.amount} to merchant {merchant_wallet.user}",
            metadata={"transaction_id": str(transaction.id), "merchant_id": merchant_id, "new_balance": float(payer_wallet.balance)},
        )
        AuditLog.log_action(
            user=transaction.user,
            action=AuditAction.UPDATE,
            target_obj=merchant_wallet,
            description=f"Payment received: +{transaction.amount} from {payer_wallet.user}",
            metadata={"transaction_id": str(transaction.id), "payer_id": str(transaction.user.id), "new_balance": float(merchant_wallet.balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _refund(transaction: Transaction):
        metadata = transaction.metadata or {}
        source_txn_id = metadata.get("source_txn_id")
        if not source_txn_id:
            raise ValidationError("Source transaction ID required for refund.")

        wallet = Wallet.objects.select_for_update().get(user=transaction.user)

        # Debit the refunding party (merchant) first, then credit the payer.
        if transaction.counterparty_id:
            refunder_wallet = Wallet.objects.select_for_update().get(user_id=transaction.counterparty_id)
            with acquire_balance_lock(refunder_wallet.user.id) or nullcontext():
                if refunder_wallet.balance < transaction.amount:
                    raise ValidationError("Insufficient balance to issue refund.")
                invalidate_cached_balance(refunder_wallet.user.id)
                refunder_wallet.balance -= transaction.amount
                refunder_wallet.save(update_fields=["balance"])
                set_cached_balance(refunder_wallet.user.id, refunder_wallet.balance)

        with acquire_balance_lock(wallet.user.id) or nullcontext():
            invalidate_cached_balance(wallet.user.id)
            wallet.balance += transaction.amount
            wallet.save(update_fields=["balance"])
            set_cached_balance(wallet.user.id, wallet.balance)

        logger.debug(f"â†©ï¸ Refund {transaction.amount} to {wallet.user} from txn {source_txn_id}")

        AuditLog.log_action(
            user=transaction.user,
            action=AuditAction.UPDATE,
            target_obj=wallet,
            description=f"Refund applied: +{transaction.amount} from transaction {source_txn_id}",
            metadata={"transaction_id": str(transaction.id), "source_txn_id": source_txn_id, "new_balance": float(wallet.balance)},
        )
