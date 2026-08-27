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

class DownloadCategory:
    """
    One counter per document TYPE, not one shared pool - e.g. downloading
    2 timetables and 2 exam results is fine even though that's 4 total,
    since timetable and exam-results each have their own limit. Matches
    the 6 document tiles on the JamiiShule Teaching Services page.
    """
    SCHEME = "SCHEME"
    LESSON_PLAN = "LESSON_PLAN"
    TIMETABLE = "TIMETABLE"
    MASTER_TIMETABLE = "MASTER_TIMETABLE"
    EXAM_RESULTS = "EXAM_RESULTS"
    QUIZ_EXAM = "QUIZ_EXAM"


# New teachers get this many free downloads of each document type (PDF and
# XLSX exports of the same document share one counter) before a paid
# subscription is required for that type, so they can judge the tool's
# quality before paying.
FREE_DOWNLOAD_LIMITS = {
    DownloadCategory.SCHEME: 1,
    DownloadCategory.LESSON_PLAN: 1,
    DownloadCategory.TIMETABLE: 2,
    DownloadCategory.MASTER_TIMETABLE: 2,
    DownloadCategory.EXAM_RESULTS: 2,
    DownloadCategory.QUIZ_EXAM: 2,
}


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


def charge_subscription(subscription: TeacherSubscription, amount_override=None) -> bool:
    """
    Debit one month's fee from the teacher's JamiiWallet balance. Returns
    True and extends current_period_end by 30 days on success; returns
    False (subscription left inactive) if the wallet balance is
    insufficient or the charge otherwise fails. Idempotent per calendar
    cycle via idempotency_key, so a retried task can't double-charge.

    `amount_override`: charges this amount instead of subscription.monthly_fee
    - used only for the ADMIN test-price path (see subscription_views.py).
    Kept on a separate idempotency-key lane so it never collides with a
    real charge for the same subscription/cycle.
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
    base_idempotency_key = f"syllabus-subscription-{subscription.id}-{cycle_key}"
    if amount_override is not None:
        base_idempotency_key += "-admintest"
    idempotency_key = base_idempotency_key

    charge_amount = amount_override if amount_override is not None else subscription.monthly_fee
    metadata = {
        "purpose": "syllabus_subscription",
        "subscription_id": str(subscription.id),
        "workstation_id": str(subscription.workstation_id),
        **({"admin_test_price": True} if amount_override is not None else {}),
    }

    # PAYMENT (not WITHDRAWAL): the fee stays inside the platform, credited
    # to the revenue owner's wallet — matches the pattern used everywhere
    # else money is collected for a service (order payments, escrow
    # release), rather than sending it "outside" like a bill payment.
    txn = TransactionEngine.initiate(
        wallet=wallet,
        amount=charge_amount,
        transaction_type=Transaction.TransactionType.PAYMENT,
        initiated_by=teacher,
        counterparty=revenue_owner,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )

    if txn.status == Transaction.TransactionStatus.COMPLETED:
        # Idempotent retry of a charge that already succeeded this cycle
        # (e.g. the deposit-resume flow firing twice) - nothing left to do,
        # NOT a failure. TransactionEngine.process() would reject this
        # (it requires PENDING), so never call it on an already-terminal txn.
        subscription.last_charge_status = TeacherSubscription.ChargeStatus.SUCCESS
        subscription.last_failure_reason = ""
        subscription.save(update_fields=["last_charge_attempt_at", "last_charge_status", "last_failure_reason"])
        return True

    # A previous attempt this cycle may have failed (e.g. insufficient
    # balance) and permanently claimed this idempotency_key on a dead
    # transaction - process() can never revive a FAILED transaction.
    # Retry under a key derived from the BASE key + that dead
    # transaction's own id (never chained onto the previous derived key -
    # that grew unboundedly with each retry and eventually overflowed the
    # column's max_length after ~6 attempts in one cycle, a real failure
    # mode hit while testing the deposit-resume flow's polling). Looped,
    # not a single if-check: the freshly-derived key itself may already
    # belong to ANOTHER earlier failed retry (if this is the 3rd+ attempt
    # this cycle) - deriving from whichever failed transaction was most
    # recently seen guarantees a never-before-used key within at most a
    # couple of hops, since a brand-new transaction is always born
    # PENDING. Never risks a double-charge: a COMPLETED transaction is
    # handled above and never reaches this loop.
    while txn.status == Transaction.TransactionStatus.FAILED:
        idempotency_key = f"{base_idempotency_key}-r{txn.id}"
        txn = TransactionEngine.initiate(
            wallet=wallet,
            amount=charge_amount,
            transaction_type=Transaction.TransactionType.PAYMENT,
            initiated_by=teacher,
            counterparty=revenue_owner,
            idempotency_key=idempotency_key,
            metadata=metadata,
        )

    if txn.status == Transaction.TransactionStatus.COMPLETED:
        # Guards a theoretical race: a concurrent request completed a
        # transaction under this exact derived retry key between our
        # initiate() call above and here.
        subscription.last_charge_status = TeacherSubscription.ChargeStatus.SUCCESS
        subscription.last_failure_reason = ""
        subscription.save(update_fields=["last_charge_attempt_at", "last_charge_status", "last_failure_reason"])
        return True

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


def has_free_downloads_remaining(user, category: str) -> bool:
    """Read-only eligibility check for ONE document category - never
    mutates anything, safe to call as many times as a view needs (some
    views check it 2-3 times per request for preview/metadata purposes,
    not just the actual download gate). Actually spending a free download
    is a separate, explicit step: see consume_free_download().

    Tracked on TeacherDownloadCredits (keyed directly to the User), NOT
    TeacherWorkStation - a teacher can legitimately delete and recreate
    their workstation (e.g. changing schools), and that must not also
    reset their free-download counters."""
    from syllabus.models.teacher_download_credits import TeacherDownloadCredits

    credits, _ = TeacherDownloadCredits.objects.get_or_create(teacher=user)
    used = (credits.free_downloads_used or {}).get(category, 0)
    return used < FREE_DOWNLOAD_LIMITS.get(category, 0)


def consume_free_download(user, category: str) -> None:
    """
    Spends exactly one free-trial download credit for ONE document
    category. Call this ONLY at the point a real document has actually
    been generated and is being handed back to the user - never from
    inside a permission check (those may run more than once per request
    for preview/metadata purposes) and never for a JSON preview that
    isn't itself a download.

    No-op for admins and paid subscribers - there's nothing to consume,
    since has_full_access() already grants them unlimited access.

    select_for_update() + read-modify-write (not F()) because this is a
    per-key update inside a JSONField dict, not a flat integer column -
    locks the row so two near-simultaneous downloads of the same category
    can't race and silently lose one of the increments.
    """
    if getattr(user, "role", None) == "ADMIN" or has_full_access(user):
        return

    from django.db import transaction
    from syllabus.models.teacher_download_credits import TeacherDownloadCredits

    with transaction.atomic():
        credits, _ = TeacherDownloadCredits.objects.select_for_update().get_or_create(teacher=user)
        counts = dict(credits.free_downloads_used or {})
        counts[category] = counts.get(category, 0) + 1
        credits.free_downloads_used = counts
        credits.save(update_fields=["free_downloads_used"])
