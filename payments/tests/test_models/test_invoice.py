# payments/tests/test_models/test_invoice.py

import pytest
from decimal import Decimal
from django.utils import timezone
from payments.models.invoice import Invoice, InvoiceStatus


@pytest.mark.django_db
def test_invoice_str(user_factory):
    user = user_factory()
    invoice = Invoice.objects.create(
        invoice_number="INV-001",
        user=user,
        amount=Decimal("100.00"),
        tax=Decimal("20.00"),
        due_date=timezone.now().date() + timezone.timedelta(days=5),
    )
    expected_str = f"Invoice INV-001 ({invoice.get_status_display()}) for {user}"
    assert str(invoice) == expected_str


@pytest.mark.django_db
def test_save_calculates_total_amount(user_factory):
    user = user_factory()
    invoice = Invoice.objects.create(
        invoice_number="INV-002",
        user=user,
        amount=Decimal("50.00"),
        tax=Decimal("10.00"),
        due_date=timezone.now().date() + timezone.timedelta(days=2),
    )
    assert invoice.total_amount == Decimal("60.00")
    assert invoice.status == InvoiceStatus.PENDING  # still pending because due date not passed


@pytest.mark.django_db
def test_save_marks_overdue_if_due_date_passed(user_factory):
    user = user_factory()
    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    invoice = Invoice.objects.create(
        invoice_number="INV-003",
        user=user,
        amount=Decimal("50.00"),
        tax=Decimal("5.00"),
        due_date=yesterday,
    )
    assert invoice.total_amount == Decimal("55.00")
    assert invoice.status == InvoiceStatus.OVERDUE  # automatically marked overdue


@pytest.mark.django_db
def test_is_overdue_property(user_factory):
    user = user_factory()
    inv = Invoice.objects.create(
        invoice_number="INV-004",
        user=user,
        amount=Decimal("70.00"),
        tax=Decimal("0.00"),
        due_date=timezone.now().date() - timezone.timedelta(days=1),
    )
    assert inv.is_overdue is True
    inv.status = InvoiceStatus.PAID
    assert inv.is_overdue is False


@pytest.mark.django_db
def test_mark_as_paid_sets_status_and_paid_at(user_factory):
    user = user_factory()
    inv = Invoice.objects.create(
        invoice_number="INV-005",
        user=user,
        amount=Decimal("100.00"),
        tax=Decimal("0.00"),
        due_date=timezone.now().date() + timezone.timedelta(days=3),
    )
    assert inv.status == InvoiceStatus.PENDING
    assert inv.paid_at is None

    before_call = timezone.now()
    inv.mark_as_paid()
    assert inv.status == InvoiceStatus.PAID
    assert inv.paid_at >= before_call

    # Custom paid_at
    custom_time = timezone.now() - timezone.timedelta(days=1)
    inv.mark_as_paid(paid_at=custom_time)
    assert inv.paid_at == custom_time