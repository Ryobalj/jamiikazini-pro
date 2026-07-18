# businesses/tests/test_views/test_broker_commission.py

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from businesses.models.order import Order
from kiini.models.referral_code import ReferralCode

pytestmark = pytest.mark.django_db

ORDERS_URL = "/api/v1/orders/"


@pytest.fixture
def broker_setup(business_factory, product_factory, user_factory):
    owner = user_factory(role="PROVIDER")
    business = business_factory(owner=owner, is_verified=True, broker_commission_rate=Decimal("5.00"))
    product = product_factory(business=business, price=Decimal("1000.00"), quantity_in_stock=50)

    buyer = user_factory(role="CLIENT")
    buyer.is_identity_verified = True
    buyer.is_phone_verified = True
    buyer.save(update_fields=["is_identity_verified", "is_phone_verified"])
    buyer.wallet.balance = Decimal("100000.00")
    buyer.wallet.save(update_fields=["balance"])

    dalali = user_factory(role="CLIENT")
    referral = ReferralCode.get_or_create_for_user(dalali)

    return {"owner": owner, "business": business, "product": product, "buyer": buyer, "dalali": dalali, "referral": referral}


class TestBrokerCommissionPayout:
    def test_commission_paid_to_referrer_on_wallet_order(self, broker_setup):
        api = APIClient()
        api.force_authenticate(user=broker_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": broker_setup["business"].id,
            "notes": "",
            "referral_code": broker_setup["referral"].code,
            "items": [{"product": broker_setup["product"].id, "quantity": 2}],
        }, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        order = Order.objects.get(id=response.data["id"])
        assert order.referred_by_id == broker_setup["dalali"].id

        broker_setup["dalali"].wallet.refresh_from_db()
        # 5% of 2000 = 100.00
        assert broker_setup["dalali"].wallet.balance == Decimal("100.00")

        broker_setup["owner"].wallet.refresh_from_db()
        # owner received the full 2000 payment, then paid out 100 commission
        assert broker_setup["owner"].wallet.balance == Decimal("1900.00")

    def test_case_insensitive_code(self, broker_setup):
        api = APIClient()
        api.force_authenticate(user=broker_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": broker_setup["business"].id,
            "notes": "",
            "referral_code": broker_setup["referral"].code.lower(),
            "items": [{"product": broker_setup["product"].id, "quantity": 1}],
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        order = Order.objects.get(id=response.data["id"])
        assert order.referred_by_id == broker_setup["dalali"].id

    def test_invalid_code_silently_ignored(self, broker_setup):
        api = APIClient()
        api.force_authenticate(user=broker_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": broker_setup["business"].id,
            "notes": "",
            "referral_code": "NOTREAL1",
            "items": [{"product": broker_setup["product"].id, "quantity": 1}],
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        order = Order.objects.get(id=response.data["id"])
        assert order.referred_by_id is None

    def test_self_referral_ignored(self, broker_setup):
        own_referral = ReferralCode.get_or_create_for_user(broker_setup["buyer"])
        api = APIClient()
        api.force_authenticate(user=broker_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": broker_setup["business"].id,
            "notes": "",
            "referral_code": own_referral.code,
            "items": [{"product": broker_setup["product"].id, "quantity": 1}],
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        order = Order.objects.get(id=response.data["id"])
        assert order.referred_by_id is None

    def test_zero_commission_rate_pays_nothing(self, broker_setup):
        broker_setup["business"].broker_commission_rate = Decimal("0.00")
        broker_setup["business"].save(update_fields=["broker_commission_rate"])

        api = APIClient()
        api.force_authenticate(user=broker_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": broker_setup["business"].id,
            "notes": "",
            "referral_code": broker_setup["referral"].code,
            "items": [{"product": broker_setup["product"].id, "quantity": 1}],
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data

        broker_setup["dalali"].wallet.refresh_from_db()
        assert broker_setup["dalali"].wallet.balance == Decimal("0.00")


class TestRetailRegressionGuard:
    """Guard: an order with no referral_code behaves exactly as before this phase."""

    def test_order_without_referral_code_unaffected(self, broker_setup):
        api = APIClient()
        api.force_authenticate(user=broker_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": broker_setup["business"].id,
            "notes": "",
            "items": [{"product": broker_setup["product"].id, "quantity": 1}],
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        order = Order.objects.get(id=response.data["id"])
        assert order.referred_by_id is None

        broker_setup["owner"].wallet.refresh_from_db()
        assert broker_setup["owner"].wallet.balance == Decimal("1000.00")  # full amount, no commission deducted


class TestMyReferralCodeView:
    def test_get_or_create_returns_stable_code(self, user_factory):
        user = user_factory(role="CLIENT")
        api = APIClient()
        api.force_authenticate(user=user)
        first = api.get("/api/v1/kiini/referral-code/mine/")
        second = api.get("/api/v1/kiini/referral-code/mine/")
        assert first.status_code == status.HTTP_200_OK
        assert first.data["code"] == second.data["code"]

    def test_requires_authentication(self):
        api = APIClient()
        response = api.get("/api/v1/kiini/referral-code/mine/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
