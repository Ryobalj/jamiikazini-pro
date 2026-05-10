# payments/tests/test_models/test_exchange_rate.py 

import pytest
from decimal import Decimal
from datetime import date
from payments.models.currency import Currency
from payments.models.exchange_rate import ExchangeRate


@pytest.mark.django_db
class TestExchangeRateModel:
    def create_currency(self, code):
        """Helper ya kutengeneza currency haraka."""
        return Currency.objects.create(code=code)

    def test_str_representation(self):
        base = self.create_currency("USD")
        target = self.create_currency("TZS")
        rate = ExchangeRate.objects.create(
            base_currency=base,
            target_currency=target,
            rate=Decimal("2500.12345678"),
            source="Forex API",
            effective_date=date(2025, 1, 1)
        )
        assert str(rate) == "USD ($) → TZS (Tsh) @ 2500.12345678 (kutoka 2025-01-01)"

    def test_unique_together_constraint(self):
        base = self.create_currency("KES")
        target = self.create_currency("TZS")
        ExchangeRate.objects.create(
            base_currency=base,
            target_currency=target,
            rate=Decimal("20.12345678"),
            effective_date=date(2025, 8, 1)
        )
        with pytest.raises(Exception):
            ExchangeRate.objects.create(
                base_currency=base,
                target_currency=target,
                rate=Decimal("21.00000000"),
                effective_date=date(2025, 8, 1)
            )

    def test_ordering_by_effective_date_desc(self):
        base = self.create_currency("UGX")
        target = self.create_currency("TZS")
        older = ExchangeRate.objects.create(
            base_currency=base,
            target_currency=target,
            rate=Decimal("1.00000000"),
            effective_date=date(2025, 7, 1)
        )
        newer = ExchangeRate.objects.create(
            base_currency=base,
            target_currency=target,
            rate=Decimal("2.00000000"),
            effective_date=date(2025, 8, 1)
        )
        qs = list(ExchangeRate.objects.all())
        assert qs[0] == newer
        assert qs[1] == older