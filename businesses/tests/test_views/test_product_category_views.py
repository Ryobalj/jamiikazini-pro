# businesses/tests/test_views/test_product_category_views.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from businesses.models.product_category import ProductCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email="admin@example.com", password="pass123")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def category():
    return ProductCategory.objects.create(name="Vyakula", slug="vyakula")


def test_list_categories(api_client, category):
    url = reverse("businesses:product-categories-list")
    res = api_client.get(url)
    assert res.status_code == 200
    assert res.data[0]["slug"] == category.slug


def test_retrieve_category_by_slug(api_client, category):
    url = reverse("businesses:product-categories-detail", kwargs={"slug": category.slug})
    res = api_client.get(url)
    assert res.status_code == 200
    assert res.data["name"] == category.name


def test_create_category_requires_auth(api_client):
    url = reverse("businesses:product-categories-list")
    res = api_client.post(url, {"name": "Vinywaji", "slug": "vinywaji"})
    assert res.status_code == 401  # unauthenticated


def test_create_category_authenticated(api_client, user):
    api_client.force_authenticate(user)
    url = reverse("businesses:product-categories-list")
    res = api_client.post(url, {"name": "Vinywaji", "slug": "vinywaji"})
    assert res.status_code == 201
    assert res.data["name"] == "Vinywaji"


def test_update_category(api_client, user, category):
    api_client.force_authenticate(user)
    url = reverse("businesses:product-categories-detail", kwargs={"slug": category.slug})
    res = api_client.patch(url, {"name": "New Name"})
    assert res.status_code == 200
    assert res.data["name"] == "New Name"


def test_delete_category(api_client, user, category):
    api_client.force_authenticate(user)
    url = reverse("businesses:product-categories-detail", kwargs={"slug": category.slug})
    res = api_client.delete(url)
    assert res.status_code == 204
    assert not ProductCategory.objects.filter(slug=category.slug).exists()


def test_search_category(api_client, category):
    url = reverse("businesses:product-categories-list") + "?search=vyakula"
    res = api_client.get(url)
    assert res.status_code == 200
    assert len(res.data) == 1
    assert res.data[0]["slug"] == "vyakula"


def test_ordering_category(api_client):
    ProductCategory.objects.create(name="A", slug="a")
    ProductCategory.objects.create(name="Z", slug="z")
    url = reverse("businesses:product-categories-list") + "?ordering=-name"
    res = api_client.get(url)
    assert res.status_code == 200
    assert res.data[0]["name"] == "Z"
