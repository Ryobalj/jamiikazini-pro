import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.gis.geos import Point

from accounts.models import User
from businesses.models.product import Product
from businesses.models.business import Business
from businesses.models.category import BusinessCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="provider@example.com",
        password="password123",
        role="PROVIDER"
    )


@pytest.fixture
def category():
    return BusinessCategory.objects.create(name="General", slug="general")


@pytest.fixture
def business(user, category):
    return Business.objects.create(
        name="Test Biz",
        owner=user,
        category=category,
        location=Point(39.2, -6.8),
        is_active=True
    )


@pytest.fixture
def product(business):
    return Product.objects.create(
        name="Sample Product",
        slug="sample-product",
        business=business,
        price=1500,
        is_available=True
    )


def test_product_list(api_client, product, business, user):
    api_client.force_authenticate(user=user)
    url = reverse("businesses:business-products-list", kwargs={"business_pk": business.pk})
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
    assert any(prod["slug"] == product.slug for prod in data)


def test_product_detail(api_client, product, business, user):
    api_client.force_authenticate(user=user)
    url = reverse("businesses:business-products-detail", kwargs={"business_pk": business.pk, "slug": product.slug})
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data["slug"] == product.slug


def test_nearby_product_list(api_client, product):
    url = reverse("businesses:product-nearby-list")
    response = api_client.get(url, {"lat": -6.8, "lng": 39.2})
    assert response.status_code == 200
    assert isinstance(response.data, list)


def test_generate_product_url(api_client, product, user):
    api_client.force_authenticate(user=user)
    url = reverse("businesses:generate-product-url", kwargs={"slug": product.slug})
    response = api_client.get(url)
    assert response.status_code == 200
    assert "url" in response.data


def test_product_create_authenticated(api_client, user, business):
    api_client.force_authenticate(user=user)
    url = reverse("businesses:business-products-list", kwargs={"business_pk": business.pk})
    data = {
        "name": "New Product",
        "slug": "new-product",
        "type": "physical",
        "price": 5000,
        "business": business.id,
        "is_available": True
    }
    response = api_client.post(url, data)
    assert response.status_code == 201
    assert response.data["slug"] == "new-product"


def test_product_create_unauthenticated(api_client, business):
    url = reverse("businesses:business-products-list", kwargs={"business_pk": business.pk})
    data = {
        "name": "New Product",
        "slug": "new-product",
        "type": "physical",
        "price": 5000,
        "business": business.id,
        "is_available": True
    }
    response = api_client.post(url, data)
    assert response.status_code == 401