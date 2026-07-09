import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from businesses.models.category import BusinessCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email="admin@example.com", password="pass123")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def category():
    return BusinessCategory.objects.create(name="Salon", slug="salon")


def test_list_categories(api_client, category):
    url = reverse("businesses:business-categories-list")
    res = api_client.get(url)
    assert res.status_code == 200
    assert res.data[0]["slug"] == category.slug


def test_retrieve_category_by_slug(api_client, category):
    url = reverse("businesses:business-categories-detail", kwargs={"slug": category.slug})
    res = api_client.get(url)
    assert res.status_code == 200
    assert res.data["name"] == category.name


def test_create_category_requires_auth(api_client):
    url = reverse("businesses:business-categories-list")
    res = api_client.post(url, {"name": "Restaurant", "slug": "restaurant"})
    assert res.status_code == 401  # unauthenticated


def test_create_category_authenticated(api_client, user):
    api_client.force_authenticate(user)
    url = reverse("businesses:business-categories-list")
    res = api_client.post(url, {"name": "Grocery", "slug": "grocery"})
    assert res.status_code == 201
    assert res.data["name"] == "Grocery"


def test_update_category(api_client, user, category):
    api_client.force_authenticate(user)
    url = reverse("businesses:business-categories-detail", kwargs={"slug": category.slug})
    res = api_client.patch(url, {"name": "New Name"})
    assert res.status_code == 200
    assert res.data["name"] == "New Name"


def test_delete_category(api_client, user, category):
    api_client.force_authenticate(user)
    url = reverse("businesses:business-categories-detail", kwargs={"slug": category.slug})
    res = api_client.delete(url)
    assert res.status_code == 204
    assert not BusinessCategory.objects.filter(slug=category.slug).exists()


def test_search_category(api_client, category):
    url = reverse("businesses:business-categories-list") + "?search=salon"
    res = api_client.get(url)
    assert res.status_code == 200
    assert len(res.data) == 1
    assert res.data[0]["slug"] == "salon"


def test_ordering_category(api_client):
    BusinessCategory.objects.create(name="A", slug="a")
    BusinessCategory.objects.create(name="Z", slug="z")
    url = reverse("businesses:business-categories-list") + "?ordering=-name"
    res = api_client.get(url)
    assert res.status_code == 200
    assert res.data[0]["name"] == "Z"