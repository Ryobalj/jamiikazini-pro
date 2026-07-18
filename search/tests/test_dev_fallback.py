# search/tests/test_dev_fallback.py
#
# Unlike the other files in search/tests/ (which skip entirely when
# ELASTICSEARCH_ENABLED=False), these tests specifically exercise the
# DB-fallback path used in dev/CI - the thing that used to crash with
# ConnectionError/TypeError/ValueError before search/utils/db_fallback.py
# and the per-document search() overrides were added.

import pytest
from decimal import Decimal
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from kiini.models.institution import Institution
from kiini.models.department import Department
from kiini.models.staff import StaffProfile
from businesses.models.product_price_tier import ProductPriceTier
from logistics.models.transport_provider import TransportProvider
from logistics.models.driver import Driver
from logistics.models.transport_provider_verification import TransportProviderVerification

pytestmark = pytest.mark.django_db


class TestDBFallbackSearch:
    """Unit tests for the shared fallback wrapper itself."""

    def test_execute_returns_response_with_hits_total(self, business_factory):
        from search.documents.business_document import BusinessDocument

        business_factory(name="Fallback Widget Shop", is_active=True)
        results = BusinessDocument.search().execute()

        assert results.hits.total.value >= 1
        assert len(list(results)) >= 1

    def test_query_multimatch_shorthand_filters_text(self, business_factory):
        from search.documents.business_document import BusinessDocument

        business_factory(name="Zebra Traders", is_active=True)
        business_factory(name="Completely Different", is_active=True)

        results = BusinessDocument.search().query("multi_match", query="Zebra", fields=["name"]).execute()
        names = {hit.name for hit in results}
        assert "Zebra Traders" in names
        assert "Completely Different" not in names

    def test_filter_term_shorthand(self, business_factory):
        from search.documents.business_document import BusinessDocument

        biz = business_factory(name="Term Filter Shop", is_active=True)
        results = BusinessDocument.search().filter("term", id=str(biz.id)).execute()
        assert len(list(results)) == 1

    def test_hit_supports_both_attribute_and_dict_access(self, business_factory):
        from search.documents.business_document import BusinessDocument
        from businesses.models.category import BusinessCategory

        category = BusinessCategory.objects.create(name="Fallback Cat", slug="fallback-cat-search-test")
        business_factory(name="Dual Access Shop", is_active=True, category=category)

        hit = next(h for h in BusinessDocument.search().execute() if h.name == "Dual Access Shop")
        # attribute-style (real ES hit convention)
        assert hit.category.name == "Fallback Cat"
        # dict-style (DRF's DictField.to_representation calls .items() on nested values)
        assert dict(hit.category.items())["name"] == "Fallback Cat"


class TestSearchEndpointsDoNotCrash:
    """One representative, data-populated check per bug class fixed in this audit."""

    def test_business_search_returns_uuid_ids_not_crash(self, business_factory):
        from businesses.models.category import BusinessCategory

        category = BusinessCategory.objects.create(name="Endpoint Cat", slug="endpoint-cat-search-test")
        biz = business_factory(name="Endpoint Test Biz", is_active=True, category=category)

        client = APIClient()
        response = client.get("/api/v1/search/", {"q": "Endpoint"})

        assert response.status_code == status.HTTP_200_OK
        assert any(item["id"] == str(biz.id) for item in response.data)

    def test_product_search_wholesale_category_and_uuid_id(self, business_factory, default_currency):
        from businesses.models.product import Product

        biz = business_factory(name="Wholesale Endpoint Biz", is_active=True)
        product = Product.objects.create(
            business=biz, name="Wholesale Widget", slug="wholesale-widget-search-test",
            price=Decimal("20.00"), currency=default_currency, is_available=True, quantity_in_stock=100,
        )
        ProductPriceTier.objects.create(product=product, min_quantity=Decimal("10"), unit_price=Decimal("15.00"))

        client = APIClient()
        response = client.get("/api/v1/search/products/", {"q": "Wholesale"})

        assert response.status_code == status.HTTP_200_OK
        assert any(item["id"] == str(product.id) for item in response.data["results"])

    def test_service_search_bool_query_with_real_query_objects(self, business_factory):
        from businesses.models.service import Service

        biz = business_factory(name="Service Endpoint Biz", is_active=True)
        Service.objects.create(business=biz, name="Endpoint Repair", price=Decimal("5.00"), is_available=True)

        client = APIClient()
        # exercises .query("bool", must=[Q(...), Q(...)]) with real Q objects, not dicts
        response = client.get("/api/v1/search/services/search/", {"q": "Endpoint"})

        assert response.status_code == status.HTTP_200_OK
        assert any(item["name"] == "Endpoint Repair" for item in response.data["results"])

    def test_staff_profile_search_requires_auth_and_returns_id(self, user_factory):
        institution = Institution.objects.create(name="Staff Endpoint Inst", domain="staff-endpoint-inst.local")
        department = Department.objects.create(institution=institution, name="Endpoint Dept")
        staff_user = user_factory(full_name="Endpoint Staffer")
        staff = StaffProfile.objects.create(user=staff_user, institution=institution, department=department, title="Manager", is_active=True)

        client = APIClient()
        anon_response = client.get("/api/v1/search/staff-profiles/")
        assert anon_response.status_code == status.HTTP_401_UNAUTHORIZED

        client.force_authenticate(user=staff_user)
        response = client.get("/api/v1/search/staff-profiles/")
        assert response.status_code == status.HTTP_200_OK
        assert any(item["id"] == str(staff.id) for item in response.data["results"])

    def test_driver_search_uses_owner_full_name_not_nonexistent_provider_name(self, user_factory):
        # TransportProvider has no name/license_number fields of its own -
        # this was a real AttributeError risk before prepare_transport_provider
        # was fixed to read provider.user.full_name instead.
        institution = Institution.objects.create(name="Driver Endpoint Inst", domain="driver-endpoint-inst.local")
        provider_user = user_factory(full_name="Endpoint Provider Owner")
        provider = TransportProvider.objects.create(user=provider_user, institution=institution, is_approved=True)
        driver = Driver.objects.create(
            transport_provider=provider, full_name="Endpoint Driver",
            license_number="ENDPOINT-LIC", phone_number="+255700000001", is_active=True,
        )

        client = APIClient()
        user = user_factory()
        client.force_authenticate(user=user)
        response = client.get("/api/v1/search/drivers/", {"q": "Endpoint Driver"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"], response.data
        # hit.to_dict() output carries raw Python values (e.g. UUID) pre-JSON-render,
        # unlike the DRF-serialized endpoints above which coerce to str already.
        found = next(h for h in response.data["results"] if str(h["id"]) == str(driver.id))
        assert found["transport_provider"]["name"] == "Endpoint Provider Owner"

    def test_transport_provider_verification_handles_unset_verification_links(self, user_factory):
        # nida/driving_license/vehicle/latra verification links are nullable
        # OneToOnes - this must not crash when none of them are set yet.
        institution = Institution.objects.create(name="Verification Endpoint Inst", domain="verification-endpoint-inst.local")
        tpv_user = user_factory(full_name="Endpoint Verification User")
        TransportProviderVerification.objects.create(user=tpv_user, institution=institution, overall_status="PENDING")

        client = APIClient()
        client.force_authenticate(user=tpv_user)
        response = client.get("/api/v1/search/transport-verifications/")

        assert response.status_code == status.HTTP_200_OK
