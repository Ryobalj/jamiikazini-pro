# businesses/tests/test_views/test_cash_payment.py

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from businesses.models.order import Order, PaymentStatus, PaymentMethod

pytestmark = pytest.mark.django_db

ORDERS_URL = "/api/v1/orders/"


@pytest.fixture
def cash_setup(business_factory, product_factory, user_factory):
    owner = user_factory(role="PROVIDER")
    business = business_factory(owner=owner, is_verified=True)
    product = product_factory(business=business, price=Decimal("2000.00"), quantity_in_stock=50)

    buyer = user_factory(role="CLIENT")
    buyer.is_identity_verified = True
    buyer.is_phone_verified = True
    buyer.save(update_fields=["is_identity_verified", "is_phone_verified"])
    buyer.wallet.balance = Decimal("0.00")  # cash orders must not require wallet funds at all
    buyer.wallet.save(update_fields=["balance"])

    return {"owner": owner, "business": business, "product": product, "buyer": buyer}


class TestCashOrderCreation:
    def test_cash_order_created_without_touching_wallet(self, cash_setup):
        api = APIClient()
        api.force_authenticate(user=cash_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": cash_setup["business"].id,
            "notes": "",
            "payment_method": "CASH",
            "items": [{"product": cash_setup["product"].id, "quantity": 2}],
        }, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        order = Order.objects.get(id=response.data["id"])
        assert order.payment_method == PaymentMethod.CASH
        assert order.payment_status == PaymentStatus.CASH_PENDING

        cash_setup["buyer"].wallet.refresh_from_db()
        assert cash_setup["buyer"].wallet.balance == Decimal("0.00")  # untouched, even though balance is 0

        cash_setup["owner"].wallet.refresh_from_db()
        assert cash_setup["owner"].wallet.balance == Decimal("0.00")  # untouched

    def test_cash_rejected_for_delivery(self, cash_setup):
        api = APIClient()
        api.force_authenticate(user=cash_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": cash_setup["business"].id,
            "notes": "",
            "payment_method": "CASH",
            "fulfillment_type": "DELIVERY",
            "delivery": {"vehicle_type": "boda_boda", "dropoff_lat": -6.8, "dropoff_lng": 39.28},
            "items": [{"product": cash_setup["product"].id, "quantity": 1}],
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.count() == 0

    def test_cash_rejected_for_unverified_business(self, cash_setup):
        cash_setup["business"].is_verified = False
        cash_setup["business"].save(update_fields=["is_verified"])
        api = APIClient()
        api.force_authenticate(user=cash_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": cash_setup["business"].id,
            "notes": "",
            "payment_method": "CASH",
            "items": [{"product": cash_setup["product"].id, "quantity": 1}],
        }, format="json")
        # OrderSerializer.validate()'s cash-specific business.is_verified check
        # fires before OrderViewSet.perform_create()'s own verified-business gate.
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.count() == 0

    def test_cash_rejected_with_credit_terms(self, cash_setup, business_factory):
        from businesses.models.business_credit_account import BusinessCreditAccount

        buyer_business = business_factory(owner=cash_setup["buyer"], is_verified=True)
        BusinessCreditAccount.objects.create(business=buyer_business, credit_limit=Decimal("100000.00"))

        api = APIClient()
        api.force_authenticate(user=cash_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": cash_setup["business"].id,
            "notes": "",
            "payment_method": "CASH",
            "purchasing_business": buyer_business.id,
            "payment_terms": "NET_15",
            "items": [{"product": cash_setup["product"].id, "quantity": 1}],
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.count() == 0


class TestMarkCashReceived:
    def test_owner_can_mark_received(self, cash_setup):
        api = APIClient()
        api.force_authenticate(user=cash_setup["buyer"])
        create_response = api.post(ORDERS_URL, {
            "business": cash_setup["business"].id,
            "notes": "",
            "payment_method": "CASH",
            "items": [{"product": cash_setup["product"].id, "quantity": 1}],
        }, format="json")
        order_id = create_response.data["id"]
        assert create_response.data["can_mark_cash_received"] is False  # buyer can't mark it themselves

        api.force_authenticate(user=cash_setup["owner"])
        detail_response = api.get(f"{ORDERS_URL}{order_id}/")
        assert detail_response.data["can_mark_cash_received"] is True

        mark_response = api.post(f"{ORDERS_URL}{order_id}/mark-cash-received/")
        assert mark_response.status_code == status.HTTP_200_OK, mark_response.data
        order = Order.objects.get(id=order_id)
        assert order.payment_status == PaymentStatus.PAID

    def test_non_owner_cannot_mark_received(self, cash_setup, user_factory):
        api = APIClient()
        api.force_authenticate(user=cash_setup["buyer"])
        create_response = api.post(ORDERS_URL, {
            "business": cash_setup["business"].id,
            "notes": "",
            "payment_method": "CASH",
            "items": [{"product": cash_setup["product"].id, "quantity": 1}],
        }, format="json")
        order_id = create_response.data["id"]

        stranger = user_factory(role="CLIENT")
        api.force_authenticate(user=stranger)
        # OrderViewSet.get_queryset() scopes to the requester's own orders -
        # a stranger can't even resolve the object, so this 404s, not 403s.
        response = api.post(f"{ORDERS_URL}{order_id}/mark-cash-received/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_mark_twice(self, cash_setup):
        api = APIClient()
        api.force_authenticate(user=cash_setup["buyer"])
        create_response = api.post(ORDERS_URL, {
            "business": cash_setup["business"].id,
            "notes": "",
            "payment_method": "CASH",
            "items": [{"product": cash_setup["product"].id, "quantity": 1}],
        }, format="json")
        order_id = create_response.data["id"]

        api.force_authenticate(user=cash_setup["owner"])
        api.post(f"{ORDERS_URL}{order_id}/mark-cash-received/")
        second_response = api.post(f"{ORDERS_URL}{order_id}/mark-cash-received/")
        assert second_response.status_code == status.HTTP_400_BAD_REQUEST


class TestRetailRegressionGuard:
    """Guard: normal wallet-paid checkout is completely unaffected by cash-on-pickup code."""

    def test_default_wallet_order_unaffected(self, cash_setup):
        cash_setup["buyer"].wallet.balance = Decimal("10000.00")
        cash_setup["buyer"].wallet.save(update_fields=["balance"])

        api = APIClient()
        api.force_authenticate(user=cash_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": cash_setup["business"].id,
            "notes": "",
            "items": [{"product": cash_setup["product"].id, "quantity": 2}],
        }, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["can_mark_cash_received"] is False
        order = Order.objects.get(id=response.data["id"])
        assert order.payment_method == PaymentMethod.WALLET
        assert order.payment_status == PaymentStatus.PAID

        cash_setup["buyer"].wallet.refresh_from_db()
        assert cash_setup["buyer"].wallet.balance == Decimal("6000.00")  # 10000 - 2*2000
