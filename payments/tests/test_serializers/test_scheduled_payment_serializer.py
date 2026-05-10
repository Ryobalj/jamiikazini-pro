# payments/tests/test_serializers/test_scheduled_payment_serializer.py

import pytest
from django.utils import timezone
from decimal import Decimal
from payments.serializers.scheduled_payment_serializer import ScheduledPaymentSerializer
from payments.models.scheduled_payment import ScheduledPayment

@pytest.mark.django_db
class TestScheduledPaymentSerializer:

    def test_serializer_create_valid(
        self, user_factory, payment_method_factory, currency_factory
    ):
        creator = user_factory()
        recipient = user_factory()
        currency = currency_factory()
        payment_method = payment_method_factory(owner=creator)

        data = {
            "amount": Decimal("1000.00"),
            "currency": currency.id,
            "payment_method": payment_method.id,
            "recipient_user": recipient.id,
            "schedule_date": timezone.now() + timezone.timedelta(days=1),
            "description": "Test scheduled payment",
            "metadata": {"note": "urgent"},
        }

        serializer = ScheduledPaymentSerializer(
            data=data, context={"request": type("Request", (), {"user": creator})()}
        )
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.created_by == creator
        assert instance.amount == Decimal("1000.00")
        assert instance.recipient_user.id == recipient.id
        assert instance.status == ScheduledPayment.Status.SCHEDULED
        assert instance.is_due is False
        assert instance.can_be_cancelled is True

    def test_serializer_invalid_amount(self, user_factory, payment_method_factory, currency_factory):
        creator = user_factory()
        recipient = user_factory()
        currency = currency_factory()
        payment_method = payment_method_factory(owner=creator)

        data = {
            "amount": -100,
            "currency": currency.id,
            "payment_method": payment_method.id,
            "recipient_user": recipient.id,
            "schedule_date": timezone.now() + timezone.timedelta(days=1),
            "description": "Test scheduled payment",
        }

        serializer = ScheduledPaymentSerializer(
            data=data, context={"request": type("Request", (), {"user": creator})()}
        )
        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_serializer_invalid_schedule_date(self, user_factory, payment_method_factory, currency_factory):
        creator = user_factory()
        recipient = user_factory()
        currency = currency_factory()
        payment_method = payment_method_factory(owner=creator)

        data = {
            "amount": 100,
            "currency": currency.id,
            "payment_method": payment_method.id,
            "recipient_user": recipient.id,
            "schedule_date": timezone.now() - timezone.timedelta(days=1),
            "description": "Test scheduled payment",
        }

        serializer = ScheduledPaymentSerializer(
            data=data, context={"request": type("Request", (), {"user": creator})()}
        )
        assert not serializer.is_valid()
        assert "schedule_date" in serializer.errors

    def test_serializer_recipient_same_as_creator(self, user_factory, payment_method_factory, currency_factory):
        creator = user_factory()
        currency = currency_factory()
        payment_method = payment_method_factory(owner=creator)

        data = {
            "amount": 100,
            "currency": currency.id,
            "payment_method": payment_method.id,
            "recipient_user": creator.id,  # Recipient same as creator
            "schedule_date": timezone.now() + timezone.timedelta(days=1),
            "description": "Test scheduled payment",
        }

        serializer = ScheduledPaymentSerializer(
            data=data, context={"request": type("Request", (), {"user": creator})()}
        )
        assert not serializer.is_valid()
        assert "recipient_user" in serializer.errors

    def test_read_only_fields_cannot_be_overwritten(self, user_factory, payment_method_factory, currency_factory):
        creator = user_factory()
        recipient = user_factory()
        currency = currency_factory()
        payment_method = payment_method_factory(owner=creator)

        data = {
            "amount": 100,
            "currency": currency.id,
            "payment_method": payment_method.id,
            "recipient_user": recipient.id,
            "schedule_date": timezone.now() + timezone.timedelta(days=1),
            "description": "Test scheduled payment",
            # Attempt to overwrite read-only fields
            "status": ScheduledPayment.Status.COMPLETED,
            "payment_reference": "XYZ123",
            "executed_at": timezone.now(),
            "cancelled_at": timezone.now(),
            "error_message": "Error",
        }

        serializer = ScheduledPaymentSerializer(
            data=data, context={"request": type("Request", (), {"user": creator})()}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        assert instance.status == ScheduledPayment.Status.SCHEDULED
        assert instance.payment_reference == ""
        assert instance.executed_at is None
        assert instance.cancelled_at is None
        assert instance.error_message == ""

    def test_serialization_output_fields(self, user_factory, payment_method_factory, currency_factory):
        creator = user_factory()
        recipient = user_factory()
        currency = currency_factory()
        payment_method = payment_method_factory(owner=creator)

        data = {
            "amount": 1000,
            "currency": currency.id,
            "payment_method": payment_method.id,
            "recipient_user": recipient.id,
            "schedule_date": timezone.now() + timezone.timedelta(days=1),
            "description": "Test scheduled payment",
        }

        serializer = ScheduledPaymentSerializer(
            data=data, context={"request": type("Request", (), {"user": creator})()}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        output = ScheduledPaymentSerializer(instance).data

        # Computed properties
        assert output["is_due"] is False
        assert output["can_be_cancelled"] is True
        # Readable fields
        assert output["created_by_name"] == creator.get_full_name()
        assert output["recipient_user_name"] == instance.recipient_user.get_full_name()
        assert output["currency_code"] == instance.currency.code
        assert output["currency_name"] == instance.currency.name
        assert output["payment_method_name"] == instance.payment_method.name