# businesses/tests/test_models/test_informal_units.py

import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from businesses.models.product import UnitChoices, WHOLE_UNIT_TYPES

pytestmark = pytest.mark.django_db

ORDERS_URL = "/api/v1/orders/"


class TestInformalUnitChoices:
    def test_new_informal_units_are_registered(self):
        codes = {choice.value for choice in UnitChoices}
        assert {"gunia", "debe", "fungu", "roli", "bale"} <= codes

    def test_new_informal_units_are_whole_only(self):
        for code in ("gunia", "debe", "fungu", "roli", "bale"):
            assert UnitChoices(code) in WHOLE_UNIT_TYPES

    def test_existing_units_unaffected(self):
        # Retail regression guard: fractional units already in use keep working.
        for code in ("kg", "g", "l", "ml", "m", "cm", "hour", "day"):
            assert UnitChoices(code) not in WHOLE_UNIT_TYPES


class TestInformalUnitOrderValidation:
    def test_fractional_quantity_rejected_for_gunia(self, business_factory, product_factory, user_factory):
        business = business_factory(is_verified=True)
        product = product_factory(business=business, unit="gunia", price=Decimal("50000.00"), quantity_in_stock=20)
        client = user_factory(role="CLIENT")
        client.is_identity_verified = True
        client.is_phone_verified = True
        client.save(update_fields=["is_identity_verified", "is_phone_verified"])
        client.wallet.balance = Decimal("500000.00")
        client.wallet.save(update_fields=["balance"])

        api = APIClient()
        api.force_authenticate(user=client)
        response = api.post(ORDERS_URL, {
            "business": business.id,
            "notes": "",
            "items": [{"product": product.id, "quantity": 2.5}],
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_whole_quantity_of_debe_succeeds(self, business_factory, product_factory, user_factory):
        business = business_factory(is_verified=True)
        product = product_factory(business=business, unit="debe", price=Decimal("3000.00"), quantity_in_stock=50)
        client = user_factory(role="CLIENT")
        client.is_identity_verified = True
        client.is_phone_verified = True
        client.save(update_fields=["is_identity_verified", "is_phone_verified"])
        client.wallet.balance = Decimal("50000.00")
        client.wallet.save(update_fields=["balance"])

        api = APIClient()
        api.force_authenticate(user=client)
        response = api.post(ORDERS_URL, {
            "business": business.id,
            "notes": "",
            "items": [{"product": product.id, "quantity": 4}],
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Decimal(response.data["total_amount"]) == Decimal("12000.00")
