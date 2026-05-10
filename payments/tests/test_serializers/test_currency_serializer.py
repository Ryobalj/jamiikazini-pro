# payments/tests/test_serializers/test_currency_serializer.py

import pytest
from payments.models.currency import Currency
from payments.serializers.currency_serializer import CurrencySerializer


@pytest.mark.django_db
def test_currency_serializer_serialization(db):
    # Tengeneza currency halisi
    currency = Currency.objects.create(
        code="USD",
        name="US Dollar",
        symbol="$",
        country="United States",
        is_active=True,
        exchange_rate_to_tzs=2500.50,
    )

    serializer = CurrencySerializer(currency)
    data = serializer.data

    # Hakikisha fields zipo sahihi
    assert data["code"] == "USD"
    assert data["name"] == "US Dollar"
    assert data["symbol"] == "$"
    assert data["country"] == "United States"
    assert data["is_active"] is True
    assert float(data["exchange_rate_to_tzs"]) == 2500.50
    # id lazima iwepo
    assert "id" in data


@pytest.mark.django_db
def test_currency_serializer_deserialization_valid(db):
    # Data yenye code sahihi
    valid_data = {
        "code": "USD",
        "is_active": True,
        "exchange_rate_to_tzs": 2500.50,
    }

    serializer = CurrencySerializer(data=valid_data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.code == "USD"
    assert instance.exchange_rate_to_tzs == 2500.50
    assert instance.is_active is True


@pytest.mark.django_db
def test_currency_serializer_invalid_code(db):
    # Data yenye code batili
    invalid_data = {
        "code": "FAKE",
        "is_active": True,
        "exchange_rate_to_tzs": 123.45,
    }

    serializer = CurrencySerializer(data=invalid_data)
    assert not serializer.is_valid()
    assert "code" in serializer.errors
    assert "Invalid currency code" in serializer.errors["code"][0]