# syllabus/services/subscription_service.py

import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from syllabus.models.teacher_subscription import TeacherSubscription
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.services.transaction_engine import TransactionEngine

logger = logging.getLogger(__name__)


def get_or_create_subscription(workstation) -> TeacherSubscription:
    subscription, _ = TeacherSubscription.objects.get_or_create(workstation=workstation)
    return subscription


def _get_revenue_owner():
    """
    The account whose JamiiWallet receives subscription fees. Follows the
    same pattern used elsewhere in the platform (order/escrow payments
    credit a Business's owner) — since "Elimu" isn't yet registered as its
    own Business, fees go to PLATFORM_REVENUE_OWNER_EMAIL for now.
    """
    User = get_user_model()
    email = getattr(settings, "PLATFORM_REVENUE_OWNER_EMAIL", "")
    if not email:
        return None
    return User.objects.filter(email=email).first()


def charge_subscription(subscription: TeacherSubscription) -> bool:
    """
    Debit one month's fee from the teacher's JamiiWallet balance. Returns
    True and extends current_period_end by 30 days on success; returns
    False (subscription left inactive) if the wallet balance is
    insufficient or the charge otherwise fails. Idempotent per calendar
    cycle via idempotency_key, so a retried task can't double-charge.
    """
    teacher = subscription.workstation.teacher
    wallet = getattr(teacher, "wallet", None)

    subscription.last_charge_attempt_at = timezone.now()

    if wallet is None:
        subscription.last_charge_status = TeacherSubscription.ChargeStatus.FAILED
        subscription.last_failure_reason = "Teacher has no JamiiWallet."
        subscription.save(update_fields=[
            "last_charge_attempt_at", "last_charge_status", "last_failure_reason"
        ])
        logger.warning(f"Subscription charge skipped — no wallet for teacher {teacher.id}")
        return False

    revenue_owner = _get_revenue_owner()
    if revenue_owner is None or not hasattr(revenue_owner, "wallet"):
        subscription.last_charge_status = TeacherSubscription.ChargeStatus.FAILED
        subscription.last_failure_reason = "Revenue account (PLATFORM_REVENUE_OWNER_EMAIL) is not configured or has no wallet."
        subscription.save(update_fields=[
            "last_charge_attempt_at", "last_charge_status", "last_failure_reason"
        ])
        logger.error("Subscription charge skipped — no valid platform revenue owner configured.")
        return False

    cycle_key = timezone.localdate().strftime("%Y-%m")
    idempotency_key = f"syllabus-subscription-{subscription.id}-{cycle_key}"

    # PAYMENT (not WITHDRAWAL): the fee stays inside the platform, credited
    # to the revenue owner's wallet — matches the pattern used everywhere
    # else money is collected for a service (order payments, escrow
    # release), rather than sending it "outside" like a bill payment.
    txn = TransactionEngine.initiate(
        wallet=wallet,
        amount=subscription.monthly_fee,
        transaction_type=Transaction.TransactionType.PAYMENT,
        initiated_by=teacher,
        counterparty=revenue_owner,
        idempotency_key=idempotency_key,
        metadata={
            "purpose": "syllabus_subscription",
            "subscription_id": str(subscription.id),
            "workstation_id": str(subscription.workstation_id),
        },
    )

    try:
        TransactionEngine.process(txn)
    except ValidationError as e:
        subscription.last_charge_status = TeacherSubscription.ChargeStatus.FAILED
        subscription.last_failure_reason = str(e)
        subscription.is_active = False
        subscription.save(update_fields=[
            "last_charge_attempt_at", "last_charge_status", "last_failure_reason", "is_active"
        ])
        logger.info(f"Subscription charge failed for {subscription.id}: {e}")
        return False

    subscription.extend_period(days=30)
    subscription.last_charge_status = TeacherSubscription.ChargeStatus.SUCCESS
    subscription.last_failure_reason = ""
    subscription.save(update_fields=[
        "last_charge_attempt_at", "last_charge_status", "last_failure_reason",
        "is_active", "current_period_end",
    ])
    logger.info(f"Subscription charged successfully: {subscription.id}, new period_end={subscription.current_period_end}")
    return True


def has_full_access(user) -> bool:
    """Whether this user's active workstation has a currently-valid
    subscription (used by CanDownloadPDF)."""
    from syllabus.models.teacher_workstation import TeacherWorkStation

    workstation = TeacherWorkStation.objects.filter(teacher=user, is_active=True).first()
    if not workstation:
        return False

    subscription = getattr(workstation, "subscription", None)
    return bool(subscription and subscription.is_valid)
