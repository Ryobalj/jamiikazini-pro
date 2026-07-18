# businesses/tests/test_views/test_bulk_order_views.py

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from businesses.models.order import Order

pytestmark = pytest.mark.django_db

BULK_URL = "/api/v1/orders/bulk/"


@pytest.fixture
def multi_seller_setup(business_factory, product_factory, user_factory):
    owner_a = user_factory(role="PROVIDER")
    owner_b = user_factory(role="PROVIDER")
    client = user_factory(role="CLIENT")
    client.is_identity_verified = True
    client.is_phone_verified = True
    client.save(update_fields=["is_identity_verified", "is_phone_verified"])
    client.wallet.balance = Decimal("1000.00")
    client.wallet.save(update_fields=["balance"])

    business_a = business_factory(owner=owner_a, is_verified=True)
    business_b = business_factory(owner=owner_b, is_verified=True)
    product_a = product_factory(business=business_a, price=Decimal("100.00"))
    product_b = product_factory(business=business_b, price=Decimal("50.00"))

    return {
        "client": client,
        "business_a": business_a,
        "business_b": business_b,
        "product_a": product_a,
        "product_b": product_b,
    }


class TestBulkOrderCreate:
    def test_creates_one_order_per_business(self, multi_seller_setup):
        api = APIClient()
        api.force_authenticate(user=multi_seller_setup["client"])
        payload = {
            "orders": [
                {
                    "business": multi_seller_setup["business_a"].id,
                    "notes": "",
                    "items": [{"product": multi_seller_setup["product_a"].id, "quantity": 2}],
                },
                {
                    "business": multi_seller_setup["business_b"].id,
                    "notes": "",
                    "items": [{"product": multi_seller_setup["product_b"].id, "quantity": 1}],
                },
            ]
        }
        response = api.post(BULK_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert len(response.data["orders"]) == 2
        assert Order.objects.filter(client=multi_seller_setup["client"]).count() == 2

        multi_seller_setup["client"].wallet.refresh_from_db()
        # 2*100 + 1*50 = 250 deducted from balance (PICKUP -> paid immediately)
        assert multi_seller_setup["client"].wallet.balance == Decimal("750.00")

    def test_rolls_back_all_orders_when_one_item_is_invalid(self, multi_seller_setup):
        api = APIClient()
        api.force_authenticate(user=multi_seller_setup["client"])
        payload = {
            "orders": [
                {
                    "business": multi_seller_setup["business_a"].id,
                    "notes": "",
                    "items": [{"product": multi_seller_setup["product_a"].id, "quantity": 2}],
                },
                {
                    "business": multi_seller_setup["business_b"].id,
                    "notes": "",
                    # product_a doesn't belong to business_b -> should fail validation
                    "items": [{"product": multi_seller_setup["product_a"].id, "quantity": 1}],
                },
            ]
        }
        response = api.post(BULK_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.filter(client=multi_seller_setup["client"]).count() == 0

        multi_seller_setup["client"].wallet.refresh_from_db()
        assert multi_seller_setup["client"].wallet.balance == Decimal("1000.00")

    def test_rejects_when_buyer_not_identity_verified(self, multi_seller_setup):
        multi_seller_setup["client"].is_identity_verified = False
        multi_seller_setup["client"].save(update_fields=["is_identity_verified"])
        api = APIClient()
        api.force_authenticate(user=multi_seller_setup["client"])
        payload = {
            "orders": [
                {
                    "business": multi_seller_setup["business_a"].id,
                    "notes": "",
                    "items": [{"product": multi_seller_setup["product_a"].id, "quantity": 1}],
                },
            ]
        }
        response = api.post(BULK_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Order.objects.count() == 0

    def test_rejects_when_a_target_business_is_unverified(self, multi_seller_setup):
        multi_seller_setup["business_b"].is_verified = False
        multi_seller_setup["business_b"].save(update_fields=["is_verified"])
        api = APIClient()
        api.force_authenticate(user=multi_seller_setup["client"])
        payload = {
            "orders": [
                {
                    "business": multi_seller_setup["business_a"].id,
                    "notes": "",
                    "items": [{"product": multi_seller_setup["product_a"].id, "quantity": 1}],
                },
                {
                    "business": multi_seller_setup["business_b"].id,
                    "notes": "",
                    "items": [{"product": multi_seller_setup["product_b"].id, "quantity": 1}],
                },
            ]
        }
        response = api.post(BULK_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Order.objects.count() == 0

    def test_rejects_empty_orders_list(self, multi_seller_setup):
        api = APIClient()
        api.force_authenticate(user=multi_seller_setup["client"])
        response = api.post(BULK_URL, {"orders": []}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_requires_authentication(self, multi_seller_setup):
        api = APIClient()
        response = api.post(BULK_URL, {"orders": []}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
