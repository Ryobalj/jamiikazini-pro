# businesses/tests/test_views/test_b2b_orders.py

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from businesses.models.order import Order
from businesses.models.business_credit_account import BusinessCreditAccount
from businesses.models.product_price_tier import ProductPriceTier
from payments.models.invoice import Invoice, InvoiceStatus

pytestmark = pytest.mark.django_db

ORDERS_URL = "/api/v1/orders/"


@pytest.fixture
def b2b_setup(business_factory, product_factory, user_factory):
    supplier_owner = user_factory(role="PROVIDER")
    buyer_owner = user_factory(role="PROVIDER")
    buyer_owner.is_identity_verified = True
    buyer_owner.is_phone_verified = True
    buyer_owner.save(update_fields=["is_identity_verified", "is_phone_verified"])
    buyer_owner.wallet.balance = Decimal("1000.00")
    buyer_owner.wallet.save(update_fields=["balance"])

    supplier = business_factory(owner=supplier_owner, is_verified=True)
    buyer_business = business_factory(owner=buyer_owner, is_verified=True)
    product = product_factory(business=supplier, price=Decimal("20.00"), quantity_in_stock=1000)

    return {
        "supplier": supplier,
        "buyer_owner": buyer_owner,
        "buyer_business": buyer_business,
        "product": product,
    }


class TestPriceForQuantity:
    def test_falls_back_to_final_price_below_any_tier(self, product_factory):
        product = product_factory(price=Decimal("20.00"))
        ProductPriceTier.objects.create(product=product, min_quantity=Decimal("500"), unit_price=Decimal("18.00"))
        assert product.price_for_quantity(Decimal("100")) == Decimal("20.00")

    def test_uses_lower_tier_at_exact_boundary(self, product_factory):
        product = product_factory(price=Decimal("20.00"))
        ProductPriceTier.objects.create(product=product, min_quantity=Decimal("100"), unit_price=Decimal("19.00"))
        ProductPriceTier.objects.create(product=product, min_quantity=Decimal("500"), unit_price=Decimal("18.00"))
        assert product.price_for_quantity(Decimal("100")) == Decimal("19.00")
        assert product.price_for_quantity(Decimal("499")) == Decimal("19.00")

    def test_uses_highest_qualifying_tier_at_exact_boundary(self, product_factory):
        product = product_factory(price=Decimal("20.00"))
        ProductPriceTier.objects.create(product=product, min_quantity=Decimal("100"), unit_price=Decimal("19.00"))
        ProductPriceTier.objects.create(product=product, min_quantity=Decimal("500"), unit_price=Decimal("18.00"))
        assert product.price_for_quantity(Decimal("500")) == Decimal("18.00")
        assert product.price_for_quantity(Decimal("10000")) == Decimal("18.00")

    def test_wholesale_price_applies_to_any_buyer_via_order_create(self, b2b_setup):
        ProductPriceTier.objects.create(
            product=b2b_setup["product"], min_quantity=Decimal("10"), unit_price=Decimal("15.00")
        )
        api = APIClient()
        api.force_authenticate(user=b2b_setup["buyer_owner"])
        payload = {
            "business": b2b_setup["supplier"].id,
            "notes": "",
            "items": [{"product": b2b_setup["product"].id, "quantity": 10}],
        }
        response = api.post(ORDERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Decimal(response.data["total_amount"]) == Decimal("150.00")


class TestB2BCreditOrders:
    def test_creates_invoice_and_skips_wallet_payment(self, b2b_setup):
        BusinessCreditAccount.objects.create(
            business=b2b_setup["buyer_business"], credit_limit=Decimal("5000.00")
        )
        api = APIClient()
        api.force_authenticate(user=b2b_setup["buyer_owner"])
        payload = {
            "business": b2b_setup["supplier"].id,
            "notes": "",
            "purchasing_business": b2b_setup["buyer_business"].id,
            "payment_terms": "NET_15",
            "items": [{"product": b2b_setup["product"].id, "quantity": 5}],
        }
        response = api.post(ORDERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data

        order = Order.objects.get(id=response.data["id"])
        assert order.invoice is not None
        assert order.invoice.status == InvoiceStatus.PENDING
        assert order.invoice.total_amount == Decimal("100.00")

        b2b_setup["buyer_owner"].wallet.refresh_from_db()
        assert b2b_setup["buyer_owner"].wallet.balance == Decimal("1000.00")  # untouched

        credit_account = BusinessCreditAccount.objects.get(business=b2b_setup["buyer_business"])
        assert credit_account.outstanding_credit == Decimal("100.00")

    def test_rejects_when_over_credit_limit(self, b2b_setup):
        BusinessCreditAccount.objects.create(
            business=b2b_setup["buyer_business"], credit_limit=Decimal("50.00")
        )
        api = APIClient()
        api.force_authenticate(user=b2b_setup["buyer_owner"])
        payload = {
            "business": b2b_setup["supplier"].id,
            "notes": "",
            "purchasing_business": b2b_setup["buyer_business"].id,
            "payment_terms": "NET_30",
            "items": [{"product": b2b_setup["product"].id, "quantity": 5}],  # 100.00 > 50.00 limit
        }
        response = api.post(ORDERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.count() == 0

    def test_rejects_without_credit_account(self, b2b_setup):
        api = APIClient()
        api.force_authenticate(user=b2b_setup["buyer_owner"])
        payload = {
            "business": b2b_setup["supplier"].id,
            "notes": "",
            "purchasing_business": b2b_setup["buyer_business"].id,
            "payment_terms": "NET_15",
            "items": [{"product": b2b_setup["product"].id, "quantity": 1}],
        }
        response = api.post(ORDERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.count() == 0

    def test_rejects_purchasing_business_not_owned_by_user(self, b2b_setup, business_factory, user_factory):
        other_owner = user_factory(role="PROVIDER")
        other_business = business_factory(owner=other_owner, is_verified=True)
        BusinessCreditAccount.objects.create(business=other_business, credit_limit=Decimal("5000.00"))

        api = APIClient()
        api.force_authenticate(user=b2b_setup["buyer_owner"])
        payload = {
            "business": b2b_setup["supplier"].id,
            "notes": "",
            "purchasing_business": other_business.id,
            "payment_terms": "NET_15",
            "items": [{"product": b2b_setup["product"].id, "quantity": 1}],
        }
        response = api.post(ORDERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.count() == 0

    def test_rejects_unverified_purchasing_business(self, b2b_setup):
        b2b_setup["buyer_business"].is_verified = False
        b2b_setup["buyer_business"].save(update_fields=["is_verified"])
        BusinessCreditAccount.objects.create(
            business=b2b_setup["buyer_business"], credit_limit=Decimal("5000.00")
        )
        api = APIClient()
        api.force_authenticate(user=b2b_setup["buyer_owner"])
        payload = {
            "business": b2b_setup["supplier"].id,
            "notes": "",
            "purchasing_business": b2b_setup["buyer_business"].id,
            "payment_terms": "NET_15",
            "items": [{"product": b2b_setup["product"].id, "quantity": 1}],
        }
        response = api.post(ORDERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.count() == 0

    def test_rejects_credit_terms_with_delivery(self, b2b_setup):
        BusinessCreditAccount.objects.create(
            business=b2b_setup["buyer_business"], credit_limit=Decimal("5000.00")
        )
        api = APIClient()
        api.force_authenticate(user=b2b_setup["buyer_owner"])
        payload = {
            "business": b2b_setup["supplier"].id,
            "notes": "",
            "purchasing_business": b2b_setup["buyer_business"].id,
            "payment_terms": "NET_15",
            "fulfillment_type": "DELIVERY",
            "delivery": {
                "vehicle_type": "boda_boda",
                "dropoff_lat": -6.8,
                "dropoff_lng": 39.28,
            },
            "items": [{"product": b2b_setup["product"].id, "quantity": 1}],
        }
        response = api.post(ORDERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.count() == 0


class TestInvoicePay:
    def test_pay_moves_funds_and_decrements_outstanding_credit(self, b2b_setup):
        BusinessCreditAccount.objects.create(
            business=b2b_setup["buyer_business"], credit_limit=Decimal("5000.00")
        )
        api = APIClient()
        api.force_authenticate(user=b2b_setup["buyer_owner"])
        create_payload = {
            "business": b2b_setup["supplier"].id,
            "notes": "",
            "purchasing_business": b2b_setup["buyer_business"].id,
            "payment_terms": "NET_15",
            "items": [{"product": b2b_setup["product"].id, "quantity": 5}],
        }
        create_response = api.post(ORDERS_URL, create_payload, format="json")
        assert create_response.status_code == status.HTTP_201_CREATED, create_response.data
        order = Order.objects.get(id=create_response.data["id"])
        invoice_id = order.invoice.id

        pay_response = api.post(f"/api/v1/payments/invoices/{invoice_id}/pay/")
        assert pay_response.status_code == status.HTTP_200_OK, pay_response.data

        invoice = Invoice.objects.get(id=invoice_id)
        assert invoice.status == InvoiceStatus.PAID

        b2b_setup["buyer_owner"].wallet.refresh_from_db()
        assert b2b_setup["buyer_owner"].wallet.balance == Decimal("900.00")  # 1000 - 100

        b2b_setup["supplier"].owner.wallet.refresh_from_db()
        assert b2b_setup["supplier"].owner.wallet.balance == Decimal("100.00")

        credit_account = BusinessCreditAccount.objects.get(business=b2b_setup["buyer_business"])
        assert credit_account.outstanding_credit == Decimal("0.00")

    def test_pay_rejected_for_non_owner(self, b2b_setup, user_factory):
        BusinessCreditAccount.objects.create(
            business=b2b_setup["buyer_business"], credit_limit=Decimal("5000.00")
        )
        api = APIClient()
        api.force_authenticate(user=b2b_setup["buyer_owner"])
        create_response = api.post(
            ORDERS_URL,
            {
                "business": b2b_setup["supplier"].id,
                "notes": "",
                "purchasing_business": b2b_setup["buyer_business"].id,
                "payment_terms": "NET_15",
                "items": [{"product": b2b_setup["product"].id, "quantity": 1}],
            },
            format="json",
        )
        order = Order.objects.get(id=create_response.data["id"])

        stranger = user_factory(role="CLIENT")
        api.force_authenticate(user=stranger)
        pay_response = api.post(f"/api/v1/payments/invoices/{order.invoice.id}/pay/")
        # InvoiceViewSet.get_queryset() is owner-scoped (owner_field="user"), so a
        # stranger's request never resolves the object at all - 404, not 403.
        assert pay_response.status_code == status.HTTP_404_NOT_FOUND


class TestRetailRegression:
    """Guard: non-B2B checkout is completely unaffected by any Phase 5 code."""

    def test_retail_order_unaffected_by_purchasing_business_field(self, b2b_setup):
        api = APIClient()
        api.force_authenticate(user=b2b_setup["buyer_owner"])
        payload = {
            "business": b2b_setup["supplier"].id,
            "notes": "",
            "items": [{"product": b2b_setup["product"].id, "quantity": 2}],
        }
        response = api.post(ORDERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data

        order = Order.objects.get(id=response.data["id"])
        assert order.purchasing_business_id is None
        assert order.payment_terms == "IMMEDIATE"
        assert order.invoice is None
        assert order.payment_status == "PAID"

        b2b_setup["buyer_owner"].wallet.refresh_from_db()
        assert b2b_setup["buyer_owner"].wallet.balance == Decimal("960.00")  # 1000 - 2*20
