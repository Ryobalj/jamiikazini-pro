# businesses/tests/test_views/test_item_request_views.py

import pytest
from decimal import Decimal
from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.test import APIClient

from businesses.models.item_request import ItemRequest, ItemRequestStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(business_factory, product_factory, user_factory):
    owner = user_factory(role="PROVIDER")
    buyer = user_factory(role="CLIENT")
    buyer.is_identity_verified = True
    buyer.is_phone_verified = True
    buyer.save(update_fields=["is_identity_verified", "is_phone_verified"])
    business = business_factory(owner=owner, location=Point(39.28, -6.80), is_verified=True)
    product = product_factory(business=business, name="Sukari Kilo 2", price=Decimal("10.00"))
    return {"owner": owner, "buyer": buyer, "business": business, "product": product}


def _create_request(client, buyer, q="Sukari"):
    api = APIClient()
    api.force_authenticate(user=buyer)
    response = api.post(
        "/api/v1/item-requests/",
        {"q": q, "quantity": 1, "lat": -6.80, "lng": 39.28, "radius_km": 10},
        format="json",
    )
    return response


class TestItemRequestBroadcastAndClaim:
    def test_create_matches_nearby_product_and_broadcasts(self, setup):
        response = _create_request(None, setup["buyer"])
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["status"] == ItemRequestStatus.PENDING
        assert response.data["matched_products_count"] == 1

    def test_create_fails_when_nothing_matches(self, setup):
        response = _create_request(None, setup["buyer"], q="Kitu Kisichokuwepo Kabisa")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_accepts_fractional_quantity(self, setup):
        api = APIClient()
        api.force_authenticate(user=setup["buyer"])
        response = api.post(
            "/api/v1/item-requests/",
            {"q": "Sukari", "quantity": "2.5", "lat": -6.80, "lng": 39.28, "radius_km": 10},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        item_request = ItemRequest.objects.get(pk=response.data["id"])
        assert item_request.quantity == Decimal("2.500")

    def test_incoming_shows_matching_pending_request_to_business_owner(self, setup):
        _create_request(None, setup["buyer"])

        api = APIClient()
        api.force_authenticate(user=setup["owner"])
        response = api.get("/api/v1/item-requests/incoming/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["product_name_query"] == "Sukari"

    def test_incoming_empty_for_unrelated_business_owner(self, setup, user_factory):
        _create_request(None, setup["buyer"])

        other_owner = user_factory(role="PROVIDER")
        api = APIClient()
        api.force_authenticate(user=other_owner)
        response = api.get("/api/v1/item-requests/incoming/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_claim_succeeds_and_binds_product_and_business(self, setup):
        create_res = _create_request(None, setup["buyer"])
        item_request_id = create_res.data["id"]

        api = APIClient()
        api.force_authenticate(user=setup["owner"])
        response = api.post(
            f"/api/v1/item-requests/{item_request_id}/claim/",
            {"product_id": str(setup["product"].id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == ItemRequestStatus.CLAIMED
        assert response.data["claimed_by_business"] == setup["business"].id
        assert response.data["claimed_product"] == setup["product"].id

    def test_second_claim_attempt_fails_cleanly_after_first_claim(self, setup, business_factory, product_factory):
        create_res = _create_request(None, setup["buyer"])
        item_request_id = create_res.data["id"]

        # First claim succeeds.
        api1 = APIClient()
        api1.force_authenticate(user=setup["owner"])
        first = api1.post(
            f"/api/v1/item-requests/{item_request_id}/claim/",
            {"product_id": str(setup["product"].id)},
            format="json",
        )
        assert first.status_code == status.HTTP_200_OK

        # A second business, also matching, tries to claim the same request afterwards -
        # exercises the select_for_update(status=PENDING) race guard's DoesNotExist path.
        other_owner_business = business_factory(location=Point(39.28, -6.80))
        other_product = product_factory(business=other_owner_business, name="Sukari Kilo 2", price=Decimal("9.00"))
        ItemRequest.objects.filter(pk=item_request_id).update(
            matched_product_ids=[setup["product"].id, other_product.id]
        )

        api2 = APIClient()
        api2.force_authenticate(user=other_owner_business.owner)
        second = api2.post(
            f"/api/v1/item-requests/{item_request_id}/claim/",
            {"product_id": str(other_product.id)},
            format="json",
        )
        assert second.status_code == status.HTTP_400_BAD_REQUEST
        assert "tayari" in str(second.data).lower() or "already" in str(second.data).lower() or "haipo" in str(second.data).lower()

        item_request = ItemRequest.objects.get(pk=item_request_id)
        assert item_request.claimed_by_business_id == setup["business"].id

    def test_claim_rejected_for_product_not_owned_by_claimant(self, setup, business_factory, product_factory):
        create_res = _create_request(None, setup["buyer"])
        item_request_id = create_res.data["id"]

        other_owner = business_factory().owner
        api = APIClient()
        api.force_authenticate(user=other_owner)
        response = api.post(
            f"/api/v1/item-requests/{item_request_id}/claim/",
            {"product_id": str(setup["product"].id)},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
