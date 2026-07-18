import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from kiini.models.institution import Institution
from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from businesses.models.product import Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def public_business():
    institution = Institution.objects.create(name="Institution Public", domain="public.jamiikazini.com")
    owner = User.objects.create_user(email="owner@biz.com", password="pass123", institution=institution)
    business = Business.objects.create(
        name="Public Biz",
        description="Visible to all",
        owner=owner,
        institution=institution,
        is_active=True,
    )
    return business


@pytest.fixture
def inactive_business():
    institution = Institution.objects.create(name="Inactive Inst", domain="inactive.jamiikazini.com")
    owner = User.objects.create_user(email="owner@inactive.com", password="pass123", institution=institution)
    business = Business.objects.create(
        name="Inactive Biz",
        owner=owner,
        institution=institution,
        is_active=False,
    )
    return business


def test_public_business_detail_view_success(public_business):
    url = reverse("businesses:public-business-detail", kwargs={"pk": public_business.pk})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_200_OK
    assert str(response.data["id"]) == str(public_business.id)
    assert response.data["name"] == public_business.name


def test_public_business_detail_view_not_found_for_inactive(inactive_business):
    url = reverse("businesses:public-business-detail", kwargs={"pk": inactive_business.pk})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_public_business_detail_view_invalid_id():
    url = reverse("businesses:public-business-detail", kwargs={"pk": "00000000-0000-0000-0000-000000000000"})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_storefront_view_includes_available_products_only(public_business):
    category = BusinessCategory.objects.create(name="Retail Trade", slug="retail-trade-store-test")
    public_business.category = category
    public_business.save(update_fields=["category"])

    Product.objects.create(
        business=public_business, name="In Stock Item", price=Decimal("10.00"),
        is_available=True, slug="in-stock-item-store-test",
    )
    Product.objects.create(
        business=public_business, name="Hidden Item", price=Decimal("5.00"),
        is_available=False, slug="hidden-item-store-test",
    )

    url = reverse("businesses:business-storefront", kwargs={"pk": public_business.pk})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_200_OK
    product_names = [p["name"] for p in response.data["products"]]
    assert "In Stock Item" in product_names
    assert "Hidden Item" not in product_names
    assert response.data["storefront_type"] == "products"
    assert response.data["category"]["slug"] == "retail-trade-store-test"
    assert response.data["review_summary"] == {"average": None, "count": 0}


def test_storefront_view_marks_informal_category_type(public_business):
    # Slugs hizi lazima zilingane na zile za _storefront_type_for's INFORMAL_CATEGORY_SLUGS
    # (zinazoendana na seed_business_categories.py) - si za jaribio la kubuni.
    parent = BusinessCategory.objects.create(name="Informal & Individual Services", slug="informal-individual-services")
    driver_cat = BusinessCategory.objects.create(name="Driver", slug="driver", parent=parent)
    public_business.category = driver_cat
    public_business.save(update_fields=["category"])

    url = reverse("businesses:business-storefront", kwargs={"pk": public_business.pk})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["storefront_type"] == "informal"


def test_storefront_view_not_found_for_inactive(inactive_business):
    url = reverse("businesses:business-storefront", kwargs={"pk": inactive_business.pk})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_storefront_view_omits_institution_for_solo_business(public_business):
    # public_business's institution only has this one Business under it - a
    # "Part of X" link would be pointless noise for a standalone shop.
    url = reverse("businesses:business-storefront", kwargs={"pk": public_business.pk})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["institution"] is None


def test_storefront_view_includes_institution_for_multi_tenant_venue(public_business):
    # A second Business joins the same Institution - now it's a real multi-tenant
    # venue (e.g. a mall) and the storefront should surface it.
    Business.objects.create(
        name="Second Tenant Shop",
        owner=public_business.owner,
        institution=public_business.institution,
        is_active=True,
    )

    url = reverse("businesses:business-storefront", kwargs={"pk": public_business.pk})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["institution"]["id"] == str(public_business.institution.id)
    assert response.data["institution"]["tenant_count"] == 2


def test_resolve_domain_returns_storefront_for_known_domain(public_business):
    url = reverse("businesses:business-resolve-domain")
    response = APIClient().get(url, {"domain": public_business.domain})

    assert response.status_code == status.HTTP_200_OK
    assert str(response.data["id"]) == str(public_business.id)


def test_resolve_domain_404_for_unknown_domain():
    url = reverse("businesses:business-resolve-domain")
    response = APIClient().get(url, {"domain": "hakuna-duka-kama-hili"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_resolve_domain_404_for_inactive_business(inactive_business):
    url = reverse("businesses:business-resolve-domain")
    response = APIClient().get(url, {"domain": inactive_business.domain})

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_resolve_domain_requires_domain_param():
    url = reverse("businesses:business-resolve-domain")
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND