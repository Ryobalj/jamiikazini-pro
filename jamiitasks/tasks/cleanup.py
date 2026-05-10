# jamiitasks/tasks/cleanup.py

import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.db.models import Count

from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.wallet import Wallet

# Import throttle + logging helpers
from jamiitasks.utils.throttling import throttled_task, log_task_event
logger = logging.getLogger(__name__)


@shared_task(bind=True)
@throttled_task(rate_limit="1/d", redis_key="cleanup:delete_stale_pending")
def delete_stale_pending_transactions(self):
    """
    Delete transactions that have been in PENDING state for more than 24 hours.
    Throttled: once per hour.
    """
    try:
        threshold = timezone.now() - timedelta(hours=24)
        stale_txns = Transaction.objects.filter(
            status=Transaction.TransactionStatus.PENDING,
            created_at__lt=threshold
        )
        count = stale_txns.count()
        stale_txns.delete()

        msg = f"Deleted {count} stale PENDING transactions older than 24 hours."
        logger.info(msg)
        log_task_event("delete_stale_pending_transactions", "SUCCESS", msg)
        return msg

    except Exception as e:
        logger.error(f"[Cleanup] Error deleting stale transactions: {e}", exc_info=True)
        log_task_event("delete_stale_pending_transactions", "FAILURE", str(e))
        raise


@shared_task(bind=True)
@throttled_task(rate_limit="1/d", redis_key="cleanup:deactivate_empty_wallets")
def deactivate_empty_wallets(self):
    """
    Deactivate wallets with zero balance, no transaction history,
    and that were created more than 6 months ago.
    Throttled: once per day.
    """
    try:
        months_threshold = 6
        cutoff_date = timezone.now() - timedelta(days=30 * months_threshold)

        wallets = Wallet.objects.annotate(txn_count=Count('transactions')).filter(
            balance=0,
            txn_count=0,
            is_active=True,
            created_at__lt=cutoff_date
        )

        count = wallets.count()
        wallets.update(is_active=False)

        msg = f"Deactivated {count} old empty wallets created before {cutoff_date.date()}."
        logger.info(msg)
        log_task_event("deactivate_empty_wallets", "SUCCESS", msg)
        return msg

    except Exception as e:
        logger.error(f"[Cleanup] Error deactivating empty wallets: {e}", exc_info=True)
        log_task_event("deactivate_empty_wallets", "FAILURE", str(e))
        raise


@shared_task(bind=True)
@throttled_task(rate_limit="2/h", redis_key="cleanup:mark_failed_pending")
def mark_failed_long_pending_transactions(self):
    """
    Automatically mark transactions as FAILED if they’ve been PENDING for over 2 hours.
    Throttled: up to 2 runs per hour.
    """
    try:
        threshold = timezone.now() - timedelta(hours=2)
        long_pending_txns = Transaction.objects.filter(
            status=Transaction.TransactionStatus.PENDING,
            created_at__lt=threshold
        )

        count = long_pending_txns.count()
        for txn in long_pending_txns:
            txn.mark_failed()

        msg = f"Marked {count} long-pending transactions as FAILED (older than 2 hours)."
        logger.info(msg)
        log_task_event("mark_failed_long_pending_transactions", "SUCCESS", msg)
        return msg

    except Exception as e:
        logger.error(f"[Cleanup] Error marking failed transactions: {e}", exc_info=True)
        log_task_event("mark_failed_long_pending_transactions", "FAILURE", str(e))
        raise