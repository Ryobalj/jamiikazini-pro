# jamiiwallet/services/transaction_engine.py

from contextlib import contextmanager
from django.db import transaction as db_transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging

from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.wallet import Wallet
from payments.models.audit_log import AuditLog, AuditAction

# ðŸ”¹ Cache layer imports
from jamiiwallet.services.cache_utils import (
    get_cached_balance,
    set_cached_balance,
    invalidate_cached_balance,
    acquire_balance_lock,
)

logger = logging.getLogger(__name__)


@contextmanager
def _held_lock(lock):
    """
    acquire_balance_lock() already calls .acquire() and hands back a lock
    that's already held. Using `with lock:` on that (redis-py Lock) would
    re-trigger __enter__ -> acquire() a second time on the same key, which
    is what caused LockNotOwnedError on release. This just guarantees the
    already-acquired lock gets released, without acquiring it again.
    """
    try:
        yield lock
    finally:
        if lock is not None:
            try:
                lock.release()
            except Exception:
                logger.warning("Failed to release balance lock", exc_info=True)


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
                case Transaction.TransactionType.HOLD:
                    TransactionEngine._hold(transaction)
                case Transaction.TransactionType.CAPTURE:
                    TransactionEngine._capture(transaction)
                case Transaction.TransactionType.VOID:
                    TransactionEngine._void(transaction)
                case _:
                    raise ValidationError("Unsupported transaction type.")

            # âœ… Ikiwa hakuna error â€” mark as completed
            transaction.status = Transaction.TransactionStatus.COMPLETED
            transaction.updated_at = timezone.now()
            transaction.save(update_fields=["status", "updated_at"])

            # ðŸ”¹ Audit log
            AuditLog.log_action(
                user=transaction.initiated_by,
                action=AuditAction.PAYMENT if transaction.transaction_type in [
                    Transaction.TransactionType.PAYMENT,
                    Transaction.TransactionType.TRANSFER,
                    Transaction.TransactionType.CAPTURE,
                ] else AuditAction.OTHER,
                target_obj=transaction,
                description=f"Transaction processed successfully: {transaction.amount} ({transaction.transaction_type})",
                metadata={
                    "wallet_id": str(transaction.wallet_id),
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
                user=transaction.initiated_by,
                action=AuditAction.PAYMENT_RETRY,
                target_obj=transaction,
                description=f"Transaction failed: {str(e)}",
                metadata={
                    "wallet_id": str(transaction.wallet_id),
                    "txn_type": transaction.transaction_type,
                    "amount": float(transaction.amount),
                    **(transaction.metadata or {}),
                },
            )

            logger.error(f"âŒ Transaction {transaction.id} failed: {e}", exc_info=True)
            raise

    # -----------------------------------------------------------------------------------
    @staticmethod
    def initiate(
        wallet,
        amount,
        transaction_type,
        initiated_by=None,
        counterparty=None,
        metadata=None,
        idempotency_key=None,
        receipt=None,
    ) -> Transaction:
        """
        Anzisha transaction mpya (PENDING). process() ndiyo inayofanya
        mabadiliko halisi ya salio. Kama idempotency_key tayari ipo kwenye
        Transaction nyingine, ile ile inarudishwa (haiundwi mara mbili).
        """
        metadata = metadata or {}

        if idempotency_key:
            existing = Transaction.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                logger.warning(f"âš ï¸ Duplicate idempotent transaction detected: {existing.id}")
                return existing

        txn = Transaction.objects.create(
            wallet=wallet,
            initiated_by=initiated_by,
            counterparty=counterparty,
            amount=amount,
            transaction_type=transaction_type,
            status=Transaction.TransactionStatus.PENDING,
            metadata=metadata,
            idempotency_key=idempotency_key,
        )

        if receipt is not None:
            txn.receipt = receipt
            txn.save(update_fields=["_receipt"])

        AuditLog.log_action(
            user=initiated_by,
            action=AuditAction.CREATE,
            target_obj=txn,
            description=f"Transaction initiated: {txn.amount} ({transaction_type})",
            metadata={"idempotency_key": idempotency_key, **metadata},
        )

        logger.info(f"ðŸŸ¢ Transaction initiated: {txn.id}")
        return txn

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _top_up(transaction: Transaction):
        wallet = Wallet.objects.select_for_update().get(pk=transaction.wallet_id)

        # Debit the refunding party (merchant) first, then credit the payer.
        if transaction.counterparty_id:
            refunder_wallet = Wallet.objects.select_for_update().get(user_id=transaction.counterparty_id)
            with _held_lock(acquire_balance_lock(refunder_wallet.user.id)):
                if refunder_wallet.available_balance < transaction.amount:
                    raise ValidationError("Insufficient balance to issue refund.")
                invalidate_cached_balance(refunder_wallet.user.id)
                refunder_wallet.balance -= transaction.amount
                refunder_wallet.save(update_fields=["balance"])
                set_cached_balance(refunder_wallet.user.id, refunder_wallet.balance)

        with _held_lock(acquire_balance_lock(wallet.user.id)):
            invalidate_cached_balance(wallet.user.id)
            wallet.balance += transaction.amount
            wallet.save(update_fields=["balance"])
            set_cached_balance(wallet.user.id, wallet.balance)

        logger.debug(f"ðŸ’° Wallet top-up successful for {wallet.user}: +{transaction.amount}")

        AuditLog.log_action(
            user=transaction.initiated_by,
            action=AuditAction.UPDATE,
            target_obj=wallet,
            description=f"Top-up applied: +{transaction.amount}",
            metadata={"transaction_id": str(transaction.id), "new_balance": float(wallet.balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _withdraw(transaction: Transaction):
        wallet = Wallet.objects.select_for_update().get(pk=transaction.wallet_id)

        with _held_lock(acquire_balance_lock(wallet.user.id)):
            if wallet.available_balance < transaction.amount:
                raise ValidationError("Insufficient balance for withdrawal.")
            invalidate_cached_balance(wallet.user.id)
            wallet.balance -= transaction.amount
            wallet.save(update_fields=["balance"])
            set_cached_balance(wallet.user.id, wallet.balance)

        logger.debug(f"ðŸ§ Wallet withdrawal successful for {wallet.user}: -{transaction.amount}")

        AuditLog.log_action(
            user=transaction.initiated_by,
            action=AuditAction.UPDATE,
            target_obj=wallet,
            description=f"Withdrawal applied: -{transaction.amount}",
            metadata={"transaction_id": str(transaction.id), "new_balance": float(wallet.balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _transfer(transaction: Transaction):
        if not transaction.counterparty_id:
            raise ValidationError("Counterparty required for transfer.")

        sender_wallet = Wallet.objects.select_for_update().get(pk=transaction.wallet_id)
        recipient_wallet = Wallet.objects.select_for_update().get(user_id=transaction.counterparty_id)

        with _held_lock(acquire_balance_lock(sender_wallet.user.id)):
            with _held_lock(acquire_balance_lock(recipient_wallet.user.id)):
                if sender_wallet.available_balance < transaction.amount:
                    raise ValidationError("Insufficient balance for transfer.")

                invalidate_cached_balance(sender_wallet.user.id)
                invalidate_cached_balance(recipient_wallet.user.id)

                sender_wallet.balance -= transaction.amount
                recipient_wallet.balance += transaction.amount

                sender_wallet.save(update_fields=["balance"])
                recipient_wallet.save(update_fields=["balance"])

                set_cached_balance(sender_wallet.user.id, sender_wallet.balance)
                set_cached_balance(recipient_wallet.user.id, recipient_wallet.balance)

        logger.debug(f"ðŸ” Transfer {transaction.amount} from {sender_wallet.user} to {recipient_wallet.user}")

        AuditLog.log_action(
            user=transaction.initiated_by,
            action=AuditAction.UPDATE,
            target_obj=sender_wallet,
            description=f"Transfer sent: -{transaction.amount} to {recipient_wallet.user}",
            metadata={"transaction_id": str(transaction.id), "recipient_id": transaction.counterparty_id, "new_balance": float(sender_wallet.balance)},
        )
        AuditLog.log_action(
            user=transaction.initiated_by,
            action=AuditAction.UPDATE,
            target_obj=recipient_wallet,
            description=f"Transfer received: +{transaction.amount} from {sender_wallet.user}",
            metadata={"transaction_id": str(transaction.id), "sender_id": str(transaction.wallet_id), "new_balance": float(recipient_wallet.balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _payment(transaction: Transaction):
        if not transaction.counterparty_id:
            raise ValidationError("Merchant counterparty required for payment.")

        payer_wallet = Wallet.objects.select_for_update().get(pk=transaction.wallet_id)
        merchant_wallet = Wallet.objects.select_for_update().get(user_id=transaction.counterparty_id)

        with _held_lock(acquire_balance_lock(payer_wallet.user.id)):
            with _held_lock(acquire_balance_lock(merchant_wallet.user.id)):
                if payer_wallet.available_balance < transaction.amount:
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
            user=transaction.initiated_by,
            action=AuditAction.PAYMENT,
            target_obj=payer_wallet,
            description=f"Payment made: -{transaction.amount} to merchant {merchant_wallet.user}",
            metadata={"transaction_id": str(transaction.id), "merchant_id": transaction.counterparty_id, "new_balance": float(payer_wallet.balance)},
        )
        AuditLog.log_action(
            user=transaction.initiated_by,
            action=AuditAction.UPDATE,
            target_obj=merchant_wallet,
            description=f"Payment received: +{transaction.amount} from {payer_wallet.user}",
            metadata={"transaction_id": str(transaction.id), "payer_id": str(transaction.wallet_id), "new_balance": float(merchant_wallet.balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _refund(transaction: Transaction):
        metadata = transaction.metadata or {}
        source_txn_id = metadata.get("source_txn_id")
        if not source_txn_id:
            raise ValidationError("Source transaction ID required for refund.")

        wallet = Wallet.objects.select_for_update().get(pk=transaction.wallet_id)

        # Debit the refunding party (merchant) first, then credit the payer.
        if transaction.counterparty_id:
            refunder_wallet = Wallet.objects.select_for_update().get(user_id=transaction.counterparty_id)
            with _held_lock(acquire_balance_lock(refunder_wallet.user.id)):
                if refunder_wallet.available_balance < transaction.amount:
                    raise ValidationError("Insufficient balance to issue refund.")
                invalidate_cached_balance(refunder_wallet.user.id)
                refunder_wallet.balance -= transaction.amount
                refunder_wallet.save(update_fields=["balance"])
                set_cached_balance(refunder_wallet.user.id, refunder_wallet.balance)

        with _held_lock(acquire_balance_lock(wallet.user.id)):
            invalidate_cached_balance(wallet.user.id)
            wallet.balance += transaction.amount
            wallet.save(update_fields=["balance"])
            set_cached_balance(wallet.user.id, wallet.balance)

        logger.debug(f"â†©ï¸ Refund {transaction.amount} to {wallet.user} from txn {source_txn_id}")

        AuditLog.log_action(
            user=transaction.initiated_by,
            action=AuditAction.UPDATE,
            target_obj=wallet,
            description=f"Refund applied: +{transaction.amount} from transaction {source_txn_id}",
            metadata={"transaction_id": str(transaction.id), "source_txn_id": source_txn_id, "new_balance": float(wallet.balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _hold(transaction: Transaction):
        """
        Shikilia (escrow) kiasi kutoka kwenye salio linaloweza kutumika (available_balance)
        la mlipaji - balance yenyewe haigusiwi, held_balance tu ndiyo inaongezeka. Fedha
        zinabaki mali ya mlipaji mpaka zi-capture au zi-void.
        """
        wallet = Wallet.objects.select_for_update().get(pk=transaction.wallet_id)

        with _held_lock(acquire_balance_lock(wallet.user.id)):
            if wallet.available_balance < transaction.amount:
                raise ValidationError("Insufficient balance to place hold.")
            invalidate_cached_balance(wallet.user.id)
            wallet.held_balance += transaction.amount
            wallet.save(update_fields=["held_balance"])
            set_cached_balance(wallet.user.id, wallet.balance)

        logger.debug(f"ðŸ”’ Hold placed for {wallet.user}: {transaction.amount}")

        AuditLog.log_action(
            user=transaction.initiated_by,
            action=AuditAction.UPDATE,
            target_obj=wallet,
            description=f"Hold placed: {transaction.amount}",
            metadata={"transaction_id": str(transaction.id), "new_held_balance": float(wallet.held_balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _capture(transaction: Transaction):
        """
        Toa fedha zilizoshikiliwa (held_balance) kwa mlipaji na kumlipa mpokeaji
        (counterparty) - hii ndiyo hatua halisi ya uhamishaji wa fedha. Order moja
        inaweza kuwa na CAPTURE zaidi ya moja (mf. moja kwa muuzaji, moja kwa dereva)
        zinazotolewa kutoka kwenye HOLD moja au zaidi ya awali.
        """
        if not transaction.counterparty_id:
            raise ValidationError("Recipient counterparty required for capture.")

        payer_wallet = Wallet.objects.select_for_update().get(pk=transaction.wallet_id)
        recipient_wallet = Wallet.objects.select_for_update().get(user_id=transaction.counterparty_id)

        with _held_lock(acquire_balance_lock(payer_wallet.user.id)):
            with _held_lock(acquire_balance_lock(recipient_wallet.user.id)):
                if payer_wallet.held_balance < transaction.amount:
                    raise ValidationError("Held balance haitoshi kwa capture hii.")

                invalidate_cached_balance(payer_wallet.user.id)
                invalidate_cached_balance(recipient_wallet.user.id)

                payer_wallet.balance -= transaction.amount
                payer_wallet.held_balance -= transaction.amount
                recipient_wallet.balance += transaction.amount

                payer_wallet.save(update_fields=["balance", "held_balance"])
                recipient_wallet.save(update_fields=["balance"])

                set_cached_balance(payer_wallet.user.id, payer_wallet.balance)
                set_cached_balance(recipient_wallet.user.id, recipient_wallet.balance)

        logger.debug(f"ðŸ’¸ Capture {transaction.amount} from {payer_wallet.user} to {recipient_wallet.user}")

        AuditLog.log_action(
            user=transaction.initiated_by,
            action=AuditAction.PAYMENT,
            target_obj=payer_wallet,
            description=f"Hold captured: -{transaction.amount} to {recipient_wallet.user}",
            metadata={"transaction_id": str(transaction.id), "recipient_id": transaction.counterparty_id, "new_held_balance": float(payer_wallet.held_balance)},
        )
        AuditLog.log_action(
            user=transaction.initiated_by,
            action=AuditAction.UPDATE,
            target_obj=recipient_wallet,
            description=f"Capture received: +{transaction.amount} from {payer_wallet.user}",
            metadata={"transaction_id": str(transaction.id), "payer_id": str(transaction.wallet_id), "new_balance": float(recipient_wallet.balance)},
        )

    # -----------------------------------------------------------------------------------
    @staticmethod
    def _void(transaction: Transaction):
        """
        Achilia sehemu (au yote) ya fedha zilizoshikiliwa bila kuhamisha kwa mtu -
        zinarudi kuwa spendable kwa mlipaji. Balance yenyewe haigusiwi.
        """
        wallet = Wallet.objects.select_for_update().get(pk=transaction.wallet_id)

        with _held_lock(acquire_balance_lock(wallet.user.id)):
            if wallet.held_balance < transaction.amount:
                raise ValidationError("Held balance haitoshi kwa void hii.")
            invalidate_cached_balance(wallet.user.id)
            wallet.held_balance -= transaction.amount
            wallet.save(update_fields=["held_balance"])
            set_cached_balance(wallet.user.id, wallet.balance)

        logger.debug(f"ðŸ”“ Hold voided for {wallet.user}: {transaction.amount}")

        AuditLog.log_action(
            user=transaction.initiated_by,
            action=AuditAction.UPDATE,
            target_obj=wallet,
            description=f"Hold voided: {transaction.amount}",
            metadata={"transaction_id": str(transaction.id), "new_held_balance": float(wallet.held_balance)},
        )
