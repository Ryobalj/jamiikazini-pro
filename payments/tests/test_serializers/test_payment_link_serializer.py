# payments/tests/test_serializers/test_payment_link_serializer.py

import pytest
from django.utils import timezone
from decimal import Decimal
from payments.models.payment_link import PaymentLink
from payments.models.currency import Currency
from payments.serializers.payment_link_serializer import PaymentLinkSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestPaymentLinkSerializer:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="testuser", password="password")

    @pytest.fixture
    def currency(self):
        return Currency.objects.create(code="TZS", name="Tanzanian Shilling", symbol="Sh")

    @pytest.fixture
    def valid_data(self, user, currency):
        return {
            "amount": Decimal("1000.00"),
            "currency": currency.id,
            "description": "Malipo ya Jaribio",
            "link_code": "ABC123XYZ789",
            "expires_at": timezone.now() + timezone.timedelta(days=1),
            "allowed_methods": ["wallet", "mobile_money"],
        }

    def test_serializer_create_valid(self, user, valid_data):
        serializer = PaymentLinkSerializer(data=valid_data, context={"request": type("Request", (), {"user": user})()})
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.created_by == user
        assert instance.amount == Decimal("1000.00")
        assert instance.is_usable is True
        assert instance.is_expired is False
        assert instance.status == PaymentLink.Status.ACTIVE
        assert instance.allowed_methods == ["wallet", "mobile_money"]

    def test_serializer_invalid_amount(self, user, valid_data):
        valid_data["amount"] = -100
        serializer = PaymentLinkSerializer(data=valid_data, context={"request": type("Request", (), {"user": user})()})
        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_serializer_invalid_expires_at(self, user, valid_data):
        valid_data["expires_at"] = timezone.now() - timezone.timedelta(days=1)
        serializer = PaymentLinkSerializer(data=valid_data, context={"request": type("Request", (), {"user": user})()})
        assert not serializer.is_valid()
        assert "expires_at" in serializer.errors

    def test_read_only_fields_cannot_be_overwritten(self, user, valid_data):
        # Trying to set read-only status, used_by, used_at
        valid_data.update({
            "status": PaymentLink.Status.USED,
            "used_by": user.id,
            "used_at": timezone.now()
        })
        serializer = PaymentLinkSerializer(data=valid_data, context={"request": type("Request", (), {"user": user})()})
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        # read-only fields remain default
        assert instance.status == PaymentLink.Status.ACTIVE
        assert instance.used_by is None
        assert instance.used_at is None

    def test_computed_fields(self, user, valid_data):
        serializer = PaymentLinkSerializer(data=valid_data, context={"request": type("Request", (), {"user": user})()})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        data = PaymentLinkSerializer(instance).data
        assert data["is_expired"] is False
        assert data["is_usable"] is True
        assert "absolute_url" in data
        assert data["absolute_url"].endswith(instance.link_code)

    def test_defaults_for_allowed_methods(self, user, valid_data):
        valid_data.pop("allowed_methods")
        serializer = PaymentLinkSerializer(data=valid_data, context={"request": type("Request", (), {"user": user})()})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        assert instance.allowed_methods == ["wallet", "mobile_money"]