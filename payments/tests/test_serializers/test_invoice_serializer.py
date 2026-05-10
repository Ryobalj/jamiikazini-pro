# payments/tests/test_serializers/test_invoice_serializer.py

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from payments.serializers.invoice_serializer import InvoiceSerializer
from payments.models.invoice import Invoice, InvoiceStatus


pytestmark = pytest.mark.django_db


def test_invoice_serializer_basic_fields(user_factory):
    user = user_factory()
    invoice = Invoice.objects.create(
        user=user,
        amount=1000,
        tax=100,
        total_amount=1100,
        status=InvoiceStatus.PENDING,
        due_date=timezone.now().date() + timezone.timedelta(days=5),
        description="Test invoice",
        created_by=user,
        last_modified_by=user,
    )

    serializer = InvoiceSerializer(instance=invoice)
    data = serializer.data

    assert data["id"] == str(invoice.id)
    assert data["invoice_number"] == invoice.invoice_number
    assert data["amount"] == "1000.00"
    assert data["tax"] == "100.00"
    assert data["total_amount"] == "1100.00"
    assert data["status"] == InvoiceStatus.PENDING
    assert data["status_display"] == "Pending"
    assert data["is_overdue"] is False
    assert data["user"]["id"] == str(user.id)
    assert data["created_by"]["id"] == str(user.id)
    assert data["last_modified_by"]["id"] == str(user.id)


def test_validate_due_date_in_past(user_factory):
    user = user_factory()
    data = {
        "user": user.id,
        "amount": 500,
        "tax": 50,
        "due_date": timezone.now().date() - timezone.timedelta(days=1),
    }
    serializer = InvoiceSerializer(data=data)
    with pytest.raises(ValidationError) as exc:
        serializer.validate_due_date(data["due_date"])
    assert "Due date haiwezi kuwa tarehe iliyopita." in str(exc.value)


def test_validate_amount_invalid():
    serializer = InvoiceSerializer()
    with pytest.raises(ValidationError):
        serializer.validate_amount(0)
    with pytest.raises(ValidationError):
        serializer.validate_amount(-100)


def test_validate_tax_invalid():
    serializer = InvoiceSerializer()
    with pytest.raises(ValidationError):
        serializer.validate_tax(-10)


def test_create_sets_user_and_creators(user_factory, rf):
    user = user_factory()
    request = rf.post("/fake-url/")
    request.user = user

    data = {
        "amount": 1000,
        "tax": 100,
        "due_date": timezone.now().date() + timezone.timedelta(days=10),
        "description": "New invoice",
        "status": InvoiceStatus.PENDING,
    }

    serializer = InvoiceSerializer(data=data, context={"request": request})
    assert serializer.is_valid(), serializer.errors
    invoice = serializer.save()

    assert invoice.created_by == user
    assert invoice.last_modified_by == user
    assert invoice.user == user
    assert invoice.total_amount == invoice.amount + invoice.tax


def test_update_sets_last_modified_by(user_factory, rf):
    user1 = user_factory()
    user2 = user_factory()
    invoice = Invoice.objects.create(
        user=user1,
        amount=1000,
        tax=100,
        total_amount=1100,
        status=InvoiceStatus.PENDING,
        due_date=timezone.now().date() + timezone.timedelta(days=5),
        created_by=user1,
        last_modified_by=user1,
    )

    request = rf.patch("/fake-url/")
    request.user = user2

    serializer = InvoiceSerializer(
        instance=invoice,
        data={"description": "Updated invoice"},
        context={"request": request},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    updated_invoice = serializer.save()

    assert updated_invoice.last_modified_by == user2
    assert updated_invoice.description == "Updated invoice"