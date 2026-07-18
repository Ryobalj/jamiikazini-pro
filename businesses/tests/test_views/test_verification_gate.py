# businesses/tests/test_views/test_verification_gate.py
#
# Verification gate must block buying/requesting/claiming for unverified
# buyers/businesses, while leaving browsing/registration untouched.

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _order_payload(business, product, quantity=1):
    return {
        "business": business.id,
        "items": [{"product": product.id, "quantity": quantity}],
    }


class TestOrderCreationVerificationGate:
    def test_unverified_buyer_cannot_create_order(self, user_factory, business_factory, product_factory):
        buyer = user_factory(role="CLIENT")  # is_identity_verified=False by default
        buyer.wallet.balance = Decimal("1000.00")
        buyer.wallet.save(update_fields=["balance"])
        business = business_factory(is_verified=True)
        product = product_factory(business=business, price=Decimal("10.00"))

        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post("/api/v1/orders/", _order_payload(business, product), format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verified_buyer_blocked_by_unverified_business(self, user_factory, business_factory, product_factory):
        buyer = user_factory(role="CLIENT", is_identity_verified=True, is_phone_verified=True)
        buyer.wallet.balance = Decimal("1000.00")
        buyer.wallet.save(update_fields=["balance"])
        business = business_factory(is_verified=False)
        product = product_factory(business=business, price=Decimal("10.00"))

        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post("/api/v1/orders/", _order_payload(business, product), format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verified_buyer_and_business_can_transact(self, user_factory, business_factory, product_factory):
        buyer = user_factory(role="CLIENT", is_identity_verified=True, is_phone_verified=True)
        buyer.wallet.balance = Decimal("1000.00")
        buyer.wallet.save(update_fields=["balance"])
        business = business_factory(is_verified=True)
        product = product_factory(business=business, price=Decimal("10.00"))

        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post("/api/v1/orders/", _order_payload(business, product), format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data


class TestItemRequestVerificationGate:
    def test_unverified_buyer_cannot_create_item_request(self, user_factory):
        buyer = user_factory(role="CLIENT")

        api = APIClient()
        api.force_authenticate(user=buyer)
        response = api.post(
            "/api/v1/item-requests/",
            {"q": "Sukari", "quantity": 1, "lat": -6.80, "lng": 39.28, "radius_km": 10},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unverified_business_cannot_claim(self, user_factory, business_factory, product_factory):
        from django.contrib.gis.geos import Point

        owner = user_factory(role="PROVIDER")
        buyer = user_factory(role="CLIENT", is_identity_verified=True, is_phone_verified=True)
        business = business_factory(owner=owner, location=Point(39.28, -6.80), is_verified=False)
        product = product_factory(business=business, name="Sukari Kilo 2", price=Decimal("10.00"))

        api = APIClient()
        api.force_authenticate(user=buyer)
        create_res = api.post(
            "/api/v1/item-requests/",
            {"q": "Sukari", "quantity": 1, "lat": -6.80, "lng": 39.28, "radius_km": 10},
            format="json",
        )
        assert create_res.status_code == status.HTTP_201_CREATED, create_res.data

        api2 = APIClient()
        api2.force_authenticate(user=owner)
        claim_res = api2.post(
            f"/api/v1/item-requests/{create_res.data['id']}/claim/",
            {"product_id": str(product.id)},
            format="json",
        )
        assert claim_res.status_code == status.HTTP_403_FORBIDDEN
