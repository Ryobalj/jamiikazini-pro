# businesses/tests/test_views/test_import_requests.py

import pytest
from datetime import date
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from businesses.models.import_request import ImportRequest, ImportRequestStatus
from payments.models.currency import Currency
from payments.models.exchange_rate import ExchangeRate

pytestmark = pytest.mark.django_db

IMPORTS_URL = "/api/v1/import-requests/"


@pytest.fixture
def import_setup(business_factory, user_factory):
    importer_owner = user_factory(role="PROVIDER")
    importer = business_factory(owner=importer_owner, is_verified=True)
    importer.deals_in_imports = True
    importer.save(update_fields=["deals_in_imports"])

    buyer = user_factory(role="CLIENT")
    buyer.is_identity_verified = True
    buyer.is_phone_verified = True
    buyer.save(update_fields=["is_identity_verified", "is_phone_verified"])

    return {"importer_owner": importer_owner, "importer": importer, "buyer": buyer}


class TestCreateImportRequest:
    def test_buyer_creates_request(self, import_setup):
        api = APIClient()
        api.force_authenticate(user=import_setup["buyer"])
        response = api.post(IMPORTS_URL, {
            "item_description": "Simu za mkononi aina ya X",
            "origin_country": "China",
            "quantity": 10,
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        req = ImportRequest.objects.get(id=response.data["id"])
        assert req.status == ImportRequestStatus.PENDING
        assert req.buyer_id == import_setup["buyer"].id
        assert req.origin_country == "China"

    def test_requires_identity_verification(self, import_setup):
        import_setup["buyer"].is_identity_verified = False
        import_setup["buyer"].save(update_fields=["is_identity_verified"])
        api = APIClient()
        api.force_authenticate(user=import_setup["buyer"])
        response = api.post(IMPORTS_URL, {
            "item_description": "Simu", "quantity": 1,
        }, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestIncomingImportRequests:
    def test_import_business_sees_pending_requests(self, import_setup):
        req = ImportRequest.objects.create(
            buyer=import_setup["buyer"], item_description="Nguo za mtumba", quantity=Decimal("5"),
        )
        api = APIClient()
        api.force_authenticate(user=import_setup["importer_owner"])
        response = api.get(f"{IMPORTS_URL}incoming/")
        assert response.status_code == status.HTTP_200_OK
        assert any(r["id"] == str(req.id) for r in response.data)

    def test_non_import_business_sees_nothing(self, import_setup, business_factory, user_factory):
        ImportRequest.objects.create(
            buyer=import_setup["buyer"], item_description="Nguo", quantity=Decimal("1"),
        )
        regular_owner = user_factory(role="PROVIDER")
        business_factory(owner=regular_owner, is_verified=True)  # deals_in_imports=False default
        api = APIClient()
        api.force_authenticate(user=regular_owner)
        response = api.get(f"{IMPORTS_URL}incoming/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []


class TestClaimImportRequest:
    def _make_request(self, buyer):
        return ImportRequest.objects.create(
            buyer=buyer, item_description="Vipuri vya gari", quantity=Decimal("2"),
        )

    def test_importer_claims_with_price_and_lead_days(self, import_setup):
        req = self._make_request(import_setup["buyer"])
        api = APIClient()
        api.force_authenticate(user=import_setup["importer_owner"])
        response = api.post(f"{IMPORTS_URL}{req.id}/claim/", {
            "business_id": str(import_setup["importer"].id),
            "price": "500000.00",
            "estimated_lead_days": 21,
        }, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        req.refresh_from_db()
        assert req.status == ImportRequestStatus.CLAIMED
        assert req.claimed_by_business_id == import_setup["importer"].id
        assert req.claimed_price == Decimal("500000.00")
        assert req.estimated_lead_days == 21

    def test_claim_converts_foreign_currency(self, import_setup, default_currency):
        usd, _ = Currency.objects.get_or_create(code="USD", defaults={"name": "US Dollar"})
        ExchangeRate.objects.create(
            base_currency=usd, target_currency=default_currency,
            rate=Decimal("2500.00"), effective_date=date.today(),
        )
        req = self._make_request(import_setup["buyer"])
        api = APIClient()
        api.force_authenticate(user=import_setup["importer_owner"])
        response = api.post(f"{IMPORTS_URL}{req.id}/claim/", {
            "business_id": str(import_setup["importer"].id),
            "price": "200.00",
            "currency_code": "USD",
            "estimated_lead_days": 30,
        }, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        req.refresh_from_db()
        assert req.claimed_price == Decimal("500000.00")  # 200 * 2500

    def test_claim_with_unknown_rate_rejected(self, import_setup):
        Currency.objects.get_or_create(code="GBP", defaults={"name": "British Pound"})
        req = self._make_request(import_setup["buyer"])
        api = APIClient()
        api.force_authenticate(user=import_setup["importer_owner"])
        response = api.post(f"{IMPORTS_URL}{req.id}/claim/", {
            "business_id": str(import_setup["importer"].id),
            "price": "100.00",
            "currency_code": "GBP",
            "estimated_lead_days": 14,
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        req.refresh_from_db()
        assert req.status == ImportRequestStatus.PENDING

    def test_cannot_claim_for_business_you_dont_own(self, import_setup, user_factory):
        req = self._make_request(import_setup["buyer"])
        stranger = user_factory(role="PROVIDER")
        api = APIClient()
        api.force_authenticate(user=stranger)
        response = api.post(f"{IMPORTS_URL}{req.id}/claim/", {
            "business_id": str(import_setup["importer"].id),
            "price": "1000.00",
            "estimated_lead_days": 7,
        }, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_import_business_cannot_claim(self, import_setup, business_factory, user_factory):
        req = self._make_request(import_setup["buyer"])
        owner = user_factory(role="PROVIDER")
        business = business_factory(owner=owner, is_verified=True)
        api = APIClient()
        api.force_authenticate(user=owner)
        response = api.post(f"{IMPORTS_URL}{req.id}/claim/", {
            "business_id": str(business.id),
            "price": "1000.00",
            "estimated_lead_days": 7,
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unverified_business_cannot_claim(self, import_setup, business_factory, user_factory):
        req = self._make_request(import_setup["buyer"])
        owner = user_factory(role="PROVIDER")
        business = business_factory(owner=owner, is_verified=False)
        business.deals_in_imports = True
        business.save(update_fields=["deals_in_imports"])
        api = APIClient()
        api.force_authenticate(user=owner)
        response = api.post(f"{IMPORTS_URL}{req.id}/claim/", {
            "business_id": str(business.id),
            "price": "1000.00",
            "estimated_lead_days": 7,
        }, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_claim_twice(self, import_setup):
        req = self._make_request(import_setup["buyer"])
        api = APIClient()
        api.force_authenticate(user=import_setup["importer_owner"])
        first = api.post(f"{IMPORTS_URL}{req.id}/claim/", {
            "business_id": str(import_setup["importer"].id),
            "price": "1000.00",
            "estimated_lead_days": 7,
        }, format="json")
        assert first.status_code == status.HTTP_200_OK
        second = api.post(f"{IMPORTS_URL}{req.id}/claim/", {
            "business_id": str(import_setup["importer"].id),
            "price": "900.00",
            "estimated_lead_days": 5,
        }, format="json")
        assert second.status_code == status.HTTP_400_BAD_REQUEST


class TestBuyerVisibility:
    def test_buyer_sees_own_requests_only(self, import_setup, user_factory):
        mine = ImportRequest.objects.create(
            buyer=import_setup["buyer"], item_description="Yangu", quantity=Decimal("1"),
        )
        other_buyer = user_factory(role="CLIENT")
        ImportRequest.objects.create(
            buyer=other_buyer, item_description="Ya mwingine", quantity=Decimal("1"),
        )
        api = APIClient()
        api.force_authenticate(user=import_setup["buyer"])
        response = api.get(IMPORTS_URL)
        assert response.status_code == status.HTTP_200_OK
        data = response.data if isinstance(response.data, list) else response.data["results"]
        ids = {r["id"] for r in data}
        assert str(mine.id) in ids
        assert len(ids) == 1
