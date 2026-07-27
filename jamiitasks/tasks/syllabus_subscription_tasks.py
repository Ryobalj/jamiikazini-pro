# jamiitasks/tasks/syllabus_subscription_tasks.py

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="jamiitasks.tasks.syllabus_subscription_tasks.renew_due_subscriptions")
def renew_due_subscriptions():
    """
    Runs daily. For every TeacherSubscription whose current period has
    reached its end date, attempt to auto-debit the next month's fee from
    the teacher's JamiiWallet balance. Succeeds silently (extends the
    period) as long as the wallet has sufficient balance — no fresh
    mobile-money prompt is needed since we're only moving money the
    teacher already deposited. On insufficient balance the subscription
    is simply left inactive until the teacher tops up and it's picked up
    on the next run.
    """
    from syllabus.models.teacher_subscription import TeacherSubscription
    from syllabus.services.subscription_service import charge_subscription

    today = timezone.localdate()
    due = TeacherSubscription.objects.filter(current_period_end__lte=today)

    renewed, failed = 0, 0
    for subscription in due:
        try:
            if charge_subscription(subscription):
                renewed += 1
            else:
                failed += 1
        except Exception:
            failed += 1
            logger.exception(f"Unexpected error renewing subscription {subscription.id}")

    logger.info(f"Subscription renewal run: {renewed} renewed, {failed} failed/insufficient, {due.count()} due total")
    return {"renewed": renewed, "failed": failed}
