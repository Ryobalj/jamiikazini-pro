# payments/tests/test_serializers/test_payment_report

import pytest
from decimal import Decimal
from datetime import date
from django.utils.formats import localize
from payments.serializers.payment_report_serializer import (
    PaymentReportSerializer,
    PaymentReportSummarySerializer,
)
from payments.models.payment_report import PaymentReport
from accounts.models import User


pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(
        username="amina", password="pass1234", email="amina@example.com"
    )


@pytest.fixture
def payment_report(user):
    report = PaymentReport.objects.create(
        user=user,
        report_date=date(2025, 1, 1),
        total_amount=Decimal("9876.54"),
        transaction_count=5,
        metadata={"source": "mobile"},
    )
    return report


def test_payment_report_serializer_output(payment_report, user):
    serializer = PaymentReportSerializer(payment_report)
    data = serializer.data

    # Linganisha id ya report kama int (sio string)
    assert data["id"] == payment_report.id

    # Linganisha user id kama string (ikiwa serializer ya user inarudisha id kama CharField)
    assert data["user"]["id"] == str(user.id)

    # Linganisha user full_name
    assert data["user"]["full_name"] == user.full_name

    # Linganisha total_amount kama string (DecimalField inarudisha string)
    assert data["total_amount"] == str(payment_report.total_amount)

    # Linganisha transaction_count
    assert data["transaction_count"] == payment_report.transaction_count


def test_payment_report_serializer_readonly_fields(payment_report):
    serializer = PaymentReportSerializer(payment_report, data={
        "user": 999,
        "formatted_total_amount": "123.45",
    }, partial=True)

    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    # confirm user not overridden
    assert instance.user == payment_report.user
    # confirm amount still same
    assert instance.total_amount == payment_report.total_amount


def test_payment_report_summary_serializer_output(payment_report):
    serializer = PaymentReportSummarySerializer(payment_report)
    data = serializer.data

    assert data["id"] == payment_report.id
    assert data["report_date"] == str(payment_report.report_date)
    assert Decimal(data["total_amount"]) == payment_report.total_amount
    assert data["transaction_count"] == 5

    # formatted amount consistency
    expected = payment_report.formatted_total_amount()
    assert data["formatted_total_amount"] == expected


def test_get_formatted_total_amount_direct(payment_report):
    serializer = PaymentReportSerializer()
    summary_serializer = PaymentReportSummarySerializer()

    # directly call helper
    assert serializer.get_formatted_total_amount(payment_report) == payment_report.formatted_total_amount()
    assert summary_serializer.get_formatted_total_amount(payment_report) == payment_report.formatted_total_amount()