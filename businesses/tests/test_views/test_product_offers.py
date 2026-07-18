# businesses/tests/test_views/test_product_offers.py

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from businesses.models.order import Order
from businesses.models.product_offer import ProductOffer, ProductOfferStatus

pytestmark = pytest.mark.django_db

OFFERS_URL = "/api/v1/product-offers/"
ORDERS_URL = "/api/v1/orders/"


@pytest.fixture
def offer_setup(business_factory, product_factory, user_factory):
    owner = user_factory(role="PROVIDER")
    business = business_factory(owner=owner, is_verified=True)
    product = product_factory(business=business, price=Decimal("1000.00"), quantity_in_stock=50)

    buyer = user_factory(role="CLIENT")
    buyer.is_identity_verified = True
    buyer.is_phone_verified = True
    buyer.save(update_fields=["is_identity_verified", "is_phone_verified"])
    buyer.wallet.balance = Decimal("100000.00")
    buyer.wallet.save(update_fields=["balance"])

    return {"owner": owner, "business": business, "product": product, "buyer": buyer}


class TestCreateOffer:
    def test_buyer_creates_offer(self, offer_setup):
        api = APIClient()
        api.force_authenticate(user=offer_setup["buyer"])
        response = api.post(OFFERS_URL, {
            "product": offer_setup["product"].id,
            "quantity": 3,
            "proposed_unit_price": "700.00",
            "note": "Naomba punguzo",
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        offer = ProductOffer.objects.get(id=response.data["id"])
        assert offer.status == ProductOfferStatus.PENDING
        assert offer.buyer_id == offer_setup["buyer"].id

    def test_requires_identity_verification(self, offer_setup):
        offer_setup["buyer"].is_identity_verified = False
        offer_setup["buyer"].save(update_fields=["is_identity_verified"])
        api = APIClient()
        api.force_authenticate(user=offer_setup["buyer"])
        response = api.post(OFFERS_URL, {
            "product": offer_setup["product"].id, "quantity": 1, "proposed_unit_price": "700.00",
        }, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestIncomingOffers:
    def test_owner_sees_pending_offers_on_own_products(self, offer_setup):
        offer = ProductOffer.objects.create(
            product=offer_setup["product"], buyer=offer_setup["buyer"],
            quantity=Decimal("2"), proposed_unit_price=Decimal("800.00"),
        )
        api = APIClient()
        api.force_authenticate(user=offer_setup["owner"])
        response = api.get(f"{OFFERS_URL}incoming/")
        assert response.status_code == status.HTTP_200_OK
        assert any(o["id"] == str(offer.id) for o in response.data)

    def test_other_business_does_not_see_offer(self, offer_setup, business_factory):
        ProductOffer.objects.create(
            product=offer_setup["product"], buyer=offer_setup["buyer"],
            quantity=Decimal("2"), proposed_unit_price=Decimal("800.00"),
        )
        other_owner = offer_setup["buyer"]  # a user who doesn't own this product's business
        api = APIClient()
        api.force_authenticate(user=other_owner)
        response = api.get(f"{OFFERS_URL}incoming/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []


class TestRespondToOffer:
    def test_owner_accepts_offer(self, offer_setup):
        offer = ProductOffer.objects.create(
            product=offer_setup["product"], buyer=offer_setup["buyer"],
            quantity=Decimal("2"), proposed_unit_price=Decimal("800.00"),
        )
        api = APIClient()
        api.force_authenticate(user=offer_setup["owner"])
        response = api.post(f"{OFFERS_URL}{offer.id}/respond/", {"decision": "ACCEPT"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        offer.refresh_from_db()
        assert offer.status == ProductOfferStatus.ACCEPTED

    def test_owner_counters_offer(self, offer_setup):
        offer = ProductOffer.objects.create(
            product=offer_setup["product"], buyer=offer_setup["buyer"],
            quantity=Decimal("2"), proposed_unit_price=Decimal("800.00"),
        )
        api = APIClient()
        api.force_authenticate(user=offer_setup["owner"])
        response = api.post(
            f"{OFFERS_URL}{offer.id}/respond/", {"decision": "COUNTER", "counter_unit_price": "900.00"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        offer.refresh_from_db()
        assert offer.status == ProductOfferStatus.COUNTERED
        assert offer.counter_unit_price == Decimal("900.00")

    def test_non_owner_cannot_respond(self, offer_setup, user_factory):
        offer = ProductOffer.objects.create(
            product=offer_setup["product"], buyer=offer_setup["buyer"],
            quantity=Decimal("2"), proposed_unit_price=Decimal("800.00"),
        )
        stranger = user_factory(role="CLIENT")
        api = APIClient()
        api.force_authenticate(user=stranger)
        response = api.post(f"{OFFERS_URL}{offer.id}/respond/", {"decision": "ACCEPT"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_buyer_accepts_counter(self, offer_setup):
        offer = ProductOffer.objects.create(
            product=offer_setup["product"], buyer=offer_setup["buyer"],
            quantity=Decimal("2"), proposed_unit_price=Decimal("800.00"),
            counter_unit_price=Decimal("900.00"), status=ProductOfferStatus.COUNTERED,
        )
        api = APIClient()
        api.force_authenticate(user=offer_setup["buyer"])
        response = api.post(f"{OFFERS_URL}{offer.id}/decide/", {"decision": "ACCEPT"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        offer.refresh_from_db()
        assert offer.status == ProductOfferStatus.ACCEPTED
        assert offer.accepted_unit_price == Decimal("900.00")

    def test_no_further_counter_after_buyer_decision(self, offer_setup):
        offer = ProductOffer.objects.create(
            product=offer_setup["product"], buyer=offer_setup["buyer"],
            quantity=Decimal("2"), proposed_unit_price=Decimal("800.00"),
            counter_unit_price=Decimal("900.00"), status=ProductOfferStatus.COUNTERED,
        )
        api = APIClient()
        api.force_authenticate(user=offer_setup["buyer"])
        api.post(f"{OFFERS_URL}{offer.id}/decide/", {"decision": "REJECT"}, format="json")

        # Seller can no longer respond after the offer is finalized.
        api.force_authenticate(user=offer_setup["owner"])
        response = api.post(f"{OFFERS_URL}{offer.id}/respond/", {"decision": "ACCEPT"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCheckoutWithAcceptedOffer:
    def test_order_uses_negotiated_price(self, offer_setup):
        offer = ProductOffer.objects.create(
            product=offer_setup["product"], buyer=offer_setup["buyer"],
            quantity=Decimal("2"), proposed_unit_price=Decimal("700.00"),
            status=ProductOfferStatus.ACCEPTED,
        )
        api = APIClient()
        api.force_authenticate(user=offer_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": offer_setup["business"].id,
            "notes": "",
            "items": [{"product": offer_setup["product"].id, "quantity": 2, "offer": offer.id}],
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Decimal(response.data["total_amount"]) == Decimal("1400.00")  # 2 * 700, not 2 * 1000

        offer.refresh_from_db()
        assert offer.consumed is True

    def test_offer_cannot_be_reused(self, offer_setup):
        offer = ProductOffer.objects.create(
            product=offer_setup["product"], buyer=offer_setup["buyer"],
            quantity=Decimal("1"), proposed_unit_price=Decimal("700.00"),
            status=ProductOfferStatus.ACCEPTED, consumed=True,
        )
        api = APIClient()
        api.force_authenticate(user=offer_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": offer_setup["business"].id,
            "notes": "",
            "items": [{"product": offer_setup["product"].id, "quantity": 1, "offer": offer.id}],
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Order.objects.count() == 0

    def test_pending_offer_cannot_be_used_for_checkout(self, offer_setup):
        offer = ProductOffer.objects.create(
            product=offer_setup["product"], buyer=offer_setup["buyer"],
            quantity=Decimal("1"), proposed_unit_price=Decimal("700.00"),
        )  # still PENDING
        api = APIClient()
        api.force_authenticate(user=offer_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": offer_setup["business"].id,
            "notes": "",
            "items": [{"product": offer_setup["product"].id, "quantity": 1, "offer": offer.id}],
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRetailRegressionGuard:
    def test_order_without_offer_uses_normal_price(self, offer_setup):
        api = APIClient()
        api.force_authenticate(user=offer_setup["buyer"])
        response = api.post(ORDERS_URL, {
            "business": offer_setup["business"].id,
            "notes": "",
            "items": [{"product": offer_setup["product"].id, "quantity": 2}],
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Decimal(response.data["total_amount"]) == Decimal("2000.00")
