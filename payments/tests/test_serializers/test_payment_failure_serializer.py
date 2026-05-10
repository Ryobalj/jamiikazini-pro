# payments/tests/test_serializers/test_payment_failure_serializer.py

import pytest
from decimal import Decimal
from django.utils.formats import localize
from payments.serializers.payment_failure_serializer import (
    PaymentFailureSerializer,
    PaymentFailureSummarySerializer,
)
from payments.models.payment_failure import PaymentFailure
from accounts.models import User
from payments.models.currency import Currency
from django.utils.formats import localize


pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(username="juma", password="test123", email="juma@example.com")


@pytest.fixture
def currency():
    return Currency.objects.create(
        code="USD", name="US Dollar", symbol="$", country="USA", is_active=True, exchange_rate_to_tzs=2500
    )


@pytest.fixture
def payment_failure(user, currency):
    return PaymentFailure.objects.create(
        user=user,
        amount=Decimal("1234.56"),
        currency=currency,
        reference="INV-1001",
        reason="Insufficient funds",
        retries=2,
    )



def test_payment_failure_serializer_output(payment_failure, user, currency):
    serializer = PaymentFailureSerializer(payment_failure)
    data = serializer.data

    # Linganisha id kama string
    assert data["id"] == str(payment_failure.id)

    # Linganisha amount kama string
    assert data["amount"] == str(payment_failure.amount)

    # Linganisha formatted_amount kutumia localize
    expected_formatted = localize(payment_failure.amount)
    assert data["formatted_amount"] == expected_formatted

    # Linganisha user
    assert data["user"]["id"] == str(payment_failure.user.id)
    assert data["user"]["full_name"] == payment_failure.user.full_name

    # Linganisha currency
    assert data["currency"]["code"] == payment_failure.currency.code

def test_payment_failure_serializer_readonly_fields(payment_failure):
    serializer = PaymentFailureSerializer(payment_failure, data={
        "user": 999,  # should be ignored
        "formatted_amount": "999.99",  # should be ignored
    }, partial=True)

    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    # values should not change
    assert instance.user == payment_failure.user
    assert instance.amount == payment_failure.amount


def test_payment_failure_summary_serializer_output(payment_failure):
    serializer = PaymentFailureSummarySerializer(payment_failure)
    data = serializer.data

    # Linganisha id kama string
    assert data["id"] == str(payment_failure.id)
    assert data["reference"] == "INV-1001"
    assert data["retries"] == 2
    assert "formatted_amount" in data

    # Linganisha formatted_amount
    from django.utils.formats import localize
    expected = localize(payment_failure.amount)
    assert data["formatted_amount"] == expected


def test_get_formatted_amount_direct(payment_failure):
    serializer = PaymentFailureSerializer()
    summary_serializer = PaymentFailureSummarySerializer()

    # call manually
    assert serializer.get_formatted_amount(payment_failure) == localize(payment_failure.amount)
    assert summary_serializer.get_formatted_amount(payment_failure) == localize(payment_failure.amount)