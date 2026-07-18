# realestate/tests/test_property_listing.py

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from payments.models.currency import Currency
from realestate.models.property_listing import PropertyListing, PropertyStatus

pytestmark = pytest.mark.django_db

PROPERTIES_URL = "/api/v1/realestate/properties/"


@pytest.fixture
def tzs(db):
    return Currency.objects.get_or_create(code="TZS")[0]


@pytest.fixture
def landlord_setup(business_factory, user_factory, tzs):
    owner = user_factory(role="PROVIDER")
    business = business_factory(owner=owner, is_verified=True)
    return {"owner": owner, "business": business, "currency": tzs}


class TestCreateListing:
    def test_owner_creates_rent_listing(self, landlord_setup):
        api = APIClient()
        api.force_authenticate(user=landlord_setup["owner"])
        response = api.post(PROPERTIES_URL, {
            "business": str(landlord_setup["business"].id),
            "listing_type": "RENT",
            "property_type": "HOUSE",
            "lat": -6.8206, "lng": 39.2806,
            "address_text": "Mikocheni, Dar es Salaam",
            "price": "300000.00",
            "deposit_amount": "300000.00",
            "currency": str(landlord_setup["currency"].id),
            "bedrooms": 3, "bathrooms": 2,
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["status"] == PropertyStatus.AVAILABLE
        listing = PropertyListing.objects.get(id=response.data["id"])
        assert listing.reservation_amount == Decimal("600000.00")

    def test_deposit_rejected_for_sale_listing(self, landlord_setup):
        api = APIClient()
        api.force_authenticate(user=landlord_setup["owner"])
        response = api.post(PROPERTIES_URL, {
            "business": str(landlord_setup["business"].id),
            "listing_type": "SALE",
            "property_type": "LAND",
            "lat": -6.8206, "lng": 39.2806,
            "price": "50000000.00",
            "deposit_amount": "1000.00",
            "currency": str(landlord_setup["currency"].id),
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_create_for_business_you_dont_own(self, landlord_setup, business_factory, user_factory):
        stranger = user_factory(role="PROVIDER")
        api = APIClient()
        api.force_authenticate(user=stranger)
        response = api.post(PROPERTIES_URL, {
            "business": str(landlord_setup["business"].id),
            "listing_type": "SALE", "property_type": "LAND",
            "lat": -6.8206, "lng": 39.2806, "price": "1000.00",
            "currency": str(landlord_setup["currency"].id),
        }, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestListingAvailabilityFiltering:
    def _make_listing(self, business, currency, status_value=PropertyStatus.AVAILABLE):
        from django.contrib.gis.geos import Point
        return PropertyListing.objects.create(
            owner=business, listing_type="SALE", property_type="LAND",
            location=Point(39.2806, -6.8206, srid=4326), price=Decimal("1000000.00"),
            currency=currency, status=status_value,
        )

    def test_available_listing_appears_in_public_list(self, landlord_setup):
        listing = self._make_listing(landlord_setup["business"], landlord_setup["currency"])
        api = APIClient()
        response = api.get(PROPERTIES_URL)
        data = response.data if isinstance(response.data, list) else response.data["results"]
        assert any(p["id"] == str(listing.id) for p in data)

    @pytest.mark.parametrize("status_value", [
        PropertyStatus.RESERVED, PropertyStatus.RENTED, PropertyStatus.SOLD,
    ])
    def test_non_available_listing_excluded_from_public_list(self, landlord_setup, status_value):
        listing = self._make_listing(landlord_setup["business"], landlord_setup["currency"], status_value)
        api = APIClient()
        response = api.get(PROPERTIES_URL)
        data = response.data if isinstance(response.data, list) else response.data["results"]
        assert not any(p["id"] == str(listing.id) for p in data)

    def test_owner_sees_all_own_listings_via_mine_regardless_of_status(self, landlord_setup):
        listing = self._make_listing(landlord_setup["business"], landlord_setup["currency"], PropertyStatus.SOLD)
        api = APIClient()
        api.force_authenticate(user=landlord_setup["owner"])
        response = api.get(f"{PROPERTIES_URL}mine/")
        ids = {p["id"] for p in response.data}
        assert str(listing.id) in ids
