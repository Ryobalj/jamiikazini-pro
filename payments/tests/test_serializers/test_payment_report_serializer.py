# payments/tests/test_serializers/test_payment_report_serializer.py
#
# Rewritten against the current PaymentReport design (report_type/status/
# date-range/async generation). The old tests targeted a long-gone model
# with report_date/total_amount/transaction_count fields.

import pytest
from datetime import timedelta
from django.utils import timezone
from payments.serializers.payment_report_serializer import (
    PaymentReportSerializer,
    PaymentReportSummarySerializer,
    PaymentReportCreateSerializer,
    PaymentReportUpdateSerializer,
)
from payments.models.payment_report import PaymentReport


pytestmark = pytest.mark.django_db


@pytest.fixture
def report_user(user_factory):
    return user_factory(full_name="Amina Report", role="CLIENT")


@pytest.fixture
def payment_report(report_user):
    end = timezone.now()
    start = end - timedelta(days=30)
    return PaymentReport.objects.create(
        user=report_user,
        report_type=PaymentReport.ReportType.TRANSACTION_SUMMARY,
        status=PaymentReport.Status.GENERATING,
        progress_percentage=50,
        start_date=start,
        end_date=end,
    )


def test_payment_report_serializer_output(payment_report, report_user):
    data = PaymentReportSerializer(payment_report).data

    assert data["id"] == str(payment_report.id)
    assert data["report_type"] == PaymentReport.ReportType.TRANSACTION_SUMMARY
    assert data["status"] == PaymentReport.Status.GENERATING
    assert data["progress_display"] == "50%"
    assert data["is_ready"] == payment_report.is_ready
    assert data["is_expired"] == payment_report.is_expired
    assert data["user"] is not None


def test_payment_report_serializer_readonly_fields(payment_report):
    serializer = PaymentReportSerializer(
        payment_report,
        data={"user": 999, "status": PaymentReport.Status.COMPLETED},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    # user is read-only and must not be overridden
    assert instance.user == payment_report.user


def test_payment_report_summary_serializer_output(payment_report):
    data = PaymentReportSummarySerializer(payment_report).data

    assert data["id"] == str(payment_report.id)
    assert data["report_type"] == PaymentReport.ReportType.TRANSACTION_SUMMARY
    assert data["duration_days"] == 30
    assert data["progress_display"] == "50%"


def test_create_serializer_rejects_reversed_dates(report_user):
    end = timezone.now()
    start = end + timedelta(days=1)  # start after end - invalid
    serializer = PaymentReportCreateSerializer(data={
        "report_type": PaymentReport.ReportType.DAILY_SUMMARY,
        "start_date": start,
        "end_date": end,
    })
    assert not serializer.is_valid()
    assert "end_date" in serializer.errors


def test_create_serializer_rejects_range_over_one_year(report_user):
    end = timezone.now()
    start = end - timedelta(days=400)
    serializer = PaymentReportCreateSerializer(data={
        "report_type": PaymentReport.ReportType.CUSTOM,
        "start_date": start,
        "end_date": end,
    })
    assert not serializer.is_valid()
    assert "end_date" in serializer.errors


def test_update_serializer_blocked_when_not_generating(payment_report):
    payment_report.status = PaymentReport.Status.COMPLETED
    payment_report.save()

    serializer = PaymentReportUpdateSerializer(
        payment_report, data={"file_format": "CSV"}, partial=True
    )
    assert not serializer.is_valid()
