# payments/tests/test_serializers/test_exchange_rate_serializer.py

import pytest
from datetime import date
from payments.models.currency import Currency
from payments.models.exchange_rate import ExchangeRate
from payments.serializers.exchange_rate_serializer import ExchangeRateSerializer


@pytest.mark.django_db
def test_exchange_rate_serializer_serialization(db):
    base = Currency.objects.create(
        code="USD", name="US Dollar", symbol="$", country="United States",
        is_active=True, exchange_rate_to_tzs=2500.0
    )
    target = Currency.objects.create(
        code="TZS", name="Tanzanian Shilling", symbol="TSh", country="Tanzania",
        is_active=True, exchange_rate_to_tzs=1.0
    )
    rate = ExchangeRate.objects.create(
        base_currency=base,
        target_currency=target,
        rate=2500.0,
        source="Bank of Tanzania",
        effective_date=date.today(),
    )

    serializer = ExchangeRateSerializer(rate)
    data = serializer.data

    assert data["base_currency"]["code"] == "USD"
    assert data["target_currency"]["code"] == "TZS"
    assert float(data["rate"]) == 2500.0
    assert data["source"] == "Bank of Tanzania"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.django_db
def test_exchange_rate_serializer_deserialization_valid(db):
    base = Currency.objects.create(
        code="USD", name="US Dollar", symbol="$", country="United States",
        is_active=True, exchange_rate_to_tzs=2500.0
    )
    target = Currency.objects.create(
        code="TZS", name="Tanzanian Shilling", symbol="TSh", country="Tanzania",
        is_active=True, exchange_rate_to_tzs=1.0
    )

    data = {
        "base_currency_id": base.id,
        "target_currency_id": target.id,
        "rate": 2500.0,
        "source": "Bank of Tanzania",
        "effective_date": str(date.today()),
    }

    serializer = ExchangeRateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.base_currency == base
    assert instance.target_currency == target
    assert instance.rate == 2500.0
    assert instance.source == "Bank of Tanzania"


@pytest.mark.django_db
def test_exchange_rate_serializer_invalid_same_currency(db):
    usd = Currency.objects.create(
        code="USD", name="US Dollar", symbol="$", country="United States",
        is_active=True, exchange_rate_to_tzs=2500.0
    )

    data = {
        "base_currency_id": usd.id,
        "target_currency_id": usd.id,
        "rate": 2000.0,
        "source": "Bank of Tanzania",
        "effective_date": str(date.today()),
    }

    serializer = ExchangeRateSerializer(data=data)
    assert not serializer.is_valid()
    assert "Sarafu ya msingi na sarafu lengwa haziwezi kuwa sawa." in str(serializer.errors)


@pytest.mark.django_db
def test_exchange_rate_serializer_invalid_rate_non_positive(db):
    usd = Currency.objects.create(
        code="USD", name="US Dollar", symbol="$", country="United States",
        is_active=True, exchange_rate_to_tzs=2500.0
    )
    tzs = Currency.objects.create(
        code="TZS", name="Tanzanian Shilling", symbol="TSh", country="Tanzania",
        is_active=True, exchange_rate_to_tzs=1.0
    )

    data = {
        "base_currency_id": usd.id,
        "target_currency_id": tzs.id,
        "rate": 0,  # invalid
        "source": "Bank of Tanzania",
        "effective_date": str(date.today()),
    }

    serializer = ExchangeRateSerializer(data=data)
    assert not serializer.is_valid()
    assert "Kiwango cha ubadilishaji lazima kiwe zaidi ya sifuri." in str(serializer.errors)