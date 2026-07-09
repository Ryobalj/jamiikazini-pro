# payments/tests/test_payment_failure.py
import pytest
from decimal import Decimal
from django.db import IntegrityError
from django.utils import timezone
from payments.models.payment_failure import PaymentFailure
pytestmark = pytest.mark.django_db


@pytest.fixture
def payment_failure(user):
    return PaymentFailure.objects.create(
        user=user,
        amount=Decimal("500.00"),
        reference="TXN12345",
        reason="Insufficient funds",
        retries=0
    )


def test_create_payment_failure(user):
    failure = PaymentFailure.objects.create(
        user=user,
        amount=Decimal("1000.50"),
        reference="TXN98765",
        reason="Network error"
    )
    assert failure.id is not None
    assert failure.user == user
    assert failure.amount == Decimal("1000.50")
    assert failure.reference == "TXN98765"
    assert failure.reason == "Network error"
    assert failure.retries == 0
    assert isinstance(failure.created_at, timezone.datetime)
    assert isinstance(failure.updated_at, timezone.datetime)


def test_str_representation(payment_failure):
    assert str(payment_failure) == "PaymentFailure(TXN12345, 500.00, retries=0)"


def test_increment_retries(payment_failure):
    payment_failure.increment_retries()
    payment_failure.refresh_from_db()
    assert payment_failure.retries == 1
    payment_failure.increment_retries()
    payment_failure.refresh_from_db()
    assert payment_failure.retries == 2


def test_unique_together_constraint(user):
    PaymentFailure.objects.create(
        user=user,
        amount=Decimal("500.00"),
        reference="TXN777",
        reason="Error"
    )
    with pytest.raises(IntegrityError):
        PaymentFailure.objects.create(
            user=user,
            amount=Decimal("300.00"),
            reference="TXN777",  # Same reference + user
            reason="Another error"
        )


def test_ordering(payment_failure, user):
    # Sukuma created_at ya rekodi ya kwanza nyuma dhahiri ili kuepuka tie ya
    # microsecond (ordering ni -created_at; rekodi mbili kwenye microsecond moja
    # huleta mpangilio usio na uhakika)
    from datetime import timedelta
    payment_failure.created_at = timezone.now() - timedelta(hours=1)
    payment_failure.save()

    newer = PaymentFailure.objects.create(
        user=user,
        amount=Decimal("100.00"),
        reference="TXNNEW",
        reason="Latest failure"
    )
    failures = list(PaymentFailure.objects.all())
    assert failures[0] == newer  # Ordered by -created_at


def test_created_and_updated_times_are_timezone_aware(payment_failure):
    assert payment_failure.created_at.tzinfo is not None
    assert payment_failure.updated_at.tzinfo is not None


def test_updated_at_changes_on_save(payment_failure):
    # Rudisha updated_at nyuma dhahiri (kupitia .update() ili kuepuka save() hook)
    # ili kuepuka tie ya microsecond kati ya updated_at ya awali na baada ya save
    from datetime import timedelta
    PaymentFailure.objects.filter(pk=payment_failure.pk).update(
        updated_at=timezone.now() - timedelta(hours=1)
    )
    payment_failure.refresh_from_db()
    old_updated = payment_failure.updated_at

    payment_failure.reason = "Updated reason"
    payment_failure.save()
    payment_failure.refresh_from_db()
    assert payment_failure.updated_at > old_updated
