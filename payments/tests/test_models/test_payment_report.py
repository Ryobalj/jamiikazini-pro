# payments/tests/test_models/test_payment_report.py

import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from payments.models.payment_report import PaymentReport

pytestmark = pytest.mark.django_db


def _report(user, **kwargs):
    defaults = dict(
        user=user,
        report_type=PaymentReport._meta.get_field("report_type").choices[0][0],
        start_date=date(2025, 1, 1),
        end_date=date(2025, 6, 30),
    )
    defaults.update(kwargs)
    return PaymentReport(**defaults)


def test_str_method(user_factory):
    user = user_factory(full_name="Ripoti Mtumiaji")
    report = _report(user)
    report.save()

    text = str(report)
    assert "Ripoti ya" in text
    assert "Ripoti Mtumiaji" in text
    assert report.get_status_display() in text


def test_clean_raises_when_start_after_end(user_factory):
    report = _report(
        user_factory(),
        start_date=date(2025, 6, 30),
        end_date=date(2025, 1, 1),
    )
    with pytest.raises(ValidationError) as exc:
        report.clean()
    assert "start_date" in exc.value.message_dict


def test_clean_raises_when_period_exceeds_one_year(user_factory):
    report = _report(
        user_factory(),
        start_date=date(2024, 1, 1),
        end_date=date(2025, 6, 30),
    )
    with pytest.raises(ValidationError) as exc:
        report.clean()
    assert "end_date" in exc.value.message_dict


def test_clean_raises_for_invalid_progress_percentage(user_factory):
    report = _report(user_factory(), progress_percentage=150)
    with pytest.raises(ValidationError) as exc:
        report.clean()
    assert "progress_percentage" in exc.value.message_dict


def test_mark_completed_and_is_ready(user_factory):
    report = _report(user_factory())
    report.save()

    report.mark_completed({"rows": []}, {"total_transactions": 3})
    report.refresh_from_db()

    assert report.status == PaymentReport.Status.COMPLETED
    assert report.progress_percentage == 100
    assert report.is_ready is True
    assert report.expires_at > timezone.now()
    assert report.get_summary_statistics()["total_transactions"] == 3


def test_is_expired(user_factory):
    report = _report(user_factory())
    report.save()
    assert not report.is_expired
    report.expires_at = timezone.now() - timedelta(days=1)
    assert report.is_expired


def test_meta_options():
    assert PaymentReport._meta.ordering == ["-created_at"]
    assert str(PaymentReport._meta.verbose_name) == "Ripoti ya Malipo"
    assert str(PaymentReport._meta.verbose_name_plural) == "Ripoti za Malipo"
