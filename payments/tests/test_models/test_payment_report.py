# payments/tests/test_models/test_payment_report.py

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import formats
from payments.models.payment_report import PaymentReport
from datetime import date

pytestmark = pytest.mark.django_db


def test_str_method_and_formatted_amount(user_factory):
    user = user_factory()
    report = PaymentReport.objects.create(
        user=user,
        report_date=date(2025, 8, 12),
        total_amount=Decimal("1234.56"),
        transaction_count=5,
        metadata={"note": "sample"}
    )

    expected_amount = formats.localize(report.total_amount)
    expected_str = (
        f"Ripoti ya Malipo ya {report.report_date} - Jumla: {expected_amount}, Idadi: {report.transaction_count}"
    )
    assert str(report) == expected_str
    assert report.formatted_total_amount() == expected_amount


def test_clean_raises_validation_error_for_negative_transaction_count(user_factory):
    report = PaymentReport(
        user=user_factory(),
        report_date=date.today(),
        total_amount=Decimal("500.00"),
        transaction_count=-1
    )

    with pytest.raises(ValidationError) as exc:
        report.clean()

    assert "haiwezi kuwa chini ya sifuri" in str(exc.value)


def test_meta_options():
    """Hakikisha Meta options ziko sawa"""
    assert PaymentReport._meta.ordering == ["-report_date"]
    assert PaymentReport._meta.verbose_name == "Payment Report"
    assert PaymentReport._meta.verbose_name_plural == "Payment Reports"