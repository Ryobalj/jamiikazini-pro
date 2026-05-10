# payments/tests/test_models/test_currency.py 

import pytest
from decimal import Decimal
from payments.models.currency import Currency


@pytest.mark.django_db
class TestCurrencyModel:
    def test_save_sets_name_symbol_and_country(self):
        currency = Currency.objects.create(code="TZS")
        assert currency.name == "Tanzanian Shilling"
        assert currency.symbol == "Tsh"
        assert currency.country == "Tanzania"

    def test_save_preserves_existing_country(self):
        currency = Currency.objects.create(code="USD", country="CustomLand")
        assert currency.name == "US Dollar"
        assert currency.symbol == "$"
        # haibadilishi country kama tayari imewekwa
        assert currency.country == "CustomLand"

    def test_str_representation(self):
        currency = Currency.objects.create(code="KES")
        assert str(currency) == "KES (KSh)"

    def test_get_by_code_returns_instance(self):
        currency = Currency.objects.create(code="UGX")
        found = Currency.get_by_code("UGX")
        assert found == currency

    def test_get_by_code_returns_none_for_invalid(self):
        assert Currency.get_by_code("XXX") is None

    def test_exchange_rate_field_accepts_decimal(self):
        currency = Currency.objects.create(code="RWF", exchange_rate_to_tzs=Decimal("2.345600"))
        assert currency.exchange_rate_to_tzs == Decimal("2.345600")

    def test_ordering_by_code(self):
        usd = Currency.objects.create(code="USD")
        kes = Currency.objects.create(code="KES")
        all_codes = list(Currency.objects.values_list("code", flat=True))
        assert all_codes == sorted(all_codes)