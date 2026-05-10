import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from businesses.models.category import BusinessCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="user@example.com",
        password="password123",
        role="INSTITUTION_ADMIN"
    )


@pytest.fixture
def category():
    return BusinessCategory.objects.create(name="Health", slug="health")


def test_category_list(api_client, category):
    url = reverse("category-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert any(cat["slug"] == category.slug for cat in response.data)


def test_category_retrieve(api_client, category):
    url = reverse("category-detail", kwargs={"slug": category.slug})
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data["slug"] == category.slug


def test_category_create_authenticated(api_client, user):
    api_client.force_authenticate(user=user)
    url = reverse("category-list")
    data = {
        "name": "Education",
        "slug": "education"
    }
    response = api_client.post(url, data)
    assert response.status_code == 201
    assert response.data["slug"] == "education"


def test_category_create_unauthenticated(api_client):
    url = reverse("category-list")
    data = {
        "name": "Finance",
        "slug": "finance"
    }
    response = api_client.post(url, data)
    assert response.status_code == 401


def test_category_update_authenticated(api_client, user, category):
    api_client.force_authenticate(user=user)
    url = reverse("category-detail", kwargs={"slug": category.slug})
    data = {
        "name": "Healthcare",
        "slug": category.slug
    }
    response = api_client.put(url, data)
    assert response.status_code == 200
    assert response.data["name"] == "Healthcare"


def test_category_delete_authenticated(api_client, user, category):
    api_client.force_authenticate(user=user)
    url = reverse("category-detail", kwargs={"slug": category.slug})
    response = api_client.delete(url)
    assert response.status_code == 204
    assert not BusinessCategory.objects.filter(slug=category.slug).exists()