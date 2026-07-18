# kiini/tests/test_institution_public.py

import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from kiini.models.institution import Institution
from businesses.models.business import Business
from businesses.models.product import Product
from businesses.models.category import BusinessCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def mall():
    return Institution.objects.create(name="Mlimani City", domain="mlimani-city.jamiikazini.com")


@pytest.fixture
def tenant_shops(mall):
    owner_a = User.objects.create_user(email="shop_a@example.com", password="pass123")
    owner_b = User.objects.create_user(email="shop_b@example.com", password="pass123")
    category = BusinessCategory.objects.create(name="Retail Trade", slug="retail-trade-mall-test")

    shop_a = Business.objects.create(
        name="Game Stores", owner=owner_a, institution=mall, category=category, is_active=True,
    )
    shop_b = Business.objects.create(
        name="Foodlovers", owner=owner_b, institution=mall, is_active=True,
    )
    Product.objects.create(
        business=shop_a, name="TV", price=Decimal("500000.00"), is_available=True, slug="tv-mall-test",
    )
    Product.objects.create(
        business=shop_a, name="Hidden", price=Decimal("1.00"), is_available=False, slug="hidden-mall-test",
    )
    return shop_a, shop_b


class TestPublicInstitutionDetailView:
    def test_returns_active_tenant_businesses_with_counts(self, mall, tenant_shops):
        shop_a, shop_b = tenant_shops
        url = reverse("kiini:institution-public-detail", kwargs={"pk": mall.pk})
        response = APIClient().get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Mlimani City"
        names = {b["name"] for b in response.data["businesses"]}
        assert names == {"Game Stores", "Foodlovers"}

        game_stores = next(b for b in response.data["businesses"] if b["name"] == "Game Stores")
        assert game_stores["category_name"] == "Retail Trade"
        assert game_stores["product_count"] == 1  # only the available one counts

    def test_excludes_inactive_tenant_businesses(self, mall, tenant_shops):
        shop_a, shop_b = tenant_shops
        shop_b.is_active = False
        shop_b.save(update_fields=["is_active"])

        url = reverse("kiini:institution-public-detail", kwargs={"pk": mall.pk})
        response = APIClient().get(url)

        names = {b["name"] for b in response.data["businesses"]}
        assert names == {"Game Stores"}

    def test_404_for_inactive_institution(self, mall):
        mall.is_active = False
        mall.save(update_fields=["is_active"])
        url = reverse("kiini:institution-public-detail", kwargs={"pk": mall.pk})
        response = APIClient().get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_no_authentication_required(self, mall, tenant_shops):
        url = reverse("kiini:institution-public-detail", kwargs={"pk": mall.pk})
        response = APIClient().get(url)  # no credentials at all
        assert response.status_code == status.HTTP_200_OK


class TestInstitutionResolveDomainView:
    def test_resolves_by_subdomain_label(self, tenant_shops):
        venue = Institution.objects.create(name="Kariakoo Center", domain="kariakoo-center")
        url = reverse("kiini:institution-resolve-domain")
        response = APIClient().get(url, {"domain": "kariakoo-center"})

        assert response.status_code == status.HTTP_200_OK
        assert str(response.data["id"]) == str(venue.id)

    def test_404_for_unknown_domain(self):
        url = reverse("kiini:institution-resolve-domain")
        response = APIClient().get(url, {"domain": "haipo-kabisa"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_404_for_inactive_institution(self):
        venue = Institution.objects.create(name="Closed Venue", domain="closed-venue", is_active=False)
        url = reverse("kiini:institution-resolve-domain")
        response = APIClient().get(url, {"domain": "closed-venue"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_domain_param(self):
        url = reverse("kiini:institution-resolve-domain")
        response = APIClient().get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
