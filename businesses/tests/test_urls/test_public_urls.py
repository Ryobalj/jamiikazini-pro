import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.gis.geos import Point

from accounts.models import User
from businesses.models.business import Business
from businesses.models.category import BusinessCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def category():
    return BusinessCategory.objects.create(name="Education", slug="education")


@pytest.fixture
def owner():
    return User.objects.create_user(
        email="owner@example.com",
        password="password123",
        role="PROVIDER"
    )


@pytest.fixture
def active_business(owner, category):
    return Business.objects.create(
        name="Visible Business",
        owner=owner,
        category=category,
        location=Point(39.2, -6.8),
        is_active=True
    )


@pytest.fixture
def inactive_business(owner, category):
    return Business.objects.create(
        name="Hidden Business",
        owner=owner,
        category=category,
        location=Point(39.3, -6.9),
        is_active=False
    )


def test_public_business_detail_success(api_client, active_business):
    url = reverse("businesses:public-business-detail", kwargs={"pk": active_business.pk})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(active_business.id)
    assert response.data["name"] == active_business.name


def test_public_business_detail_not_found(api_client, inactive_business):
    url = reverse("businesses:public-business-detail", kwargs={"pk": inactive_business.pk})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_public_business_detail_invalid_uuid(api_client):
    url = reverse("businesses:public-business-detail", kwargs={"pk": "00000000-0000-0000-0000-000000000000"})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND