import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.gis.geos import Point

from accounts.models import User
from businesses.models.business import Business
from businesses.models.service import Service
from businesses.models.category import BusinessCategory
from businesses.models.booking import Booking

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def provider():
    return User.objects.create_user(
        email="provider@example.com",
        password="pass123",
        role="PROVIDER"
    )


@pytest.fixture
def client_user():
    return User.objects.create_user(
        email="client@example.com",
        password="clientpass",
        role="CLIENT"
    )


@pytest.fixture
def category():
    return BusinessCategory.objects.create(name="Tech", slug="tech")


@pytest.fixture
def business(provider, category):
    return Business.objects.create(
        name="Tech Hub",
        owner=provider,
        category=category,
        location=Point(39.2, -6.8),
        is_active=True
    )


@pytest.fixture
def service(business):
    return Service.objects.create(
        name="Software Installation",
        business=business,
        description="Install and configure software",
        price=100.00
    )


@pytest.fixture
def booking(service, client_user):
    return Booking.objects.create(
        service=service,
        client=client_user,
        scheduled_datetime="2025-07-01T10:00:00Z",
        notes="Please install Python and VS Code",
        status="PENDING"
    )


def test_service_booking_list_as_owner(client, provider, service, booking):
    client.force_authenticate(user=provider)
    url = reverse('service-bookings-list', kwargs={'service_pk': service.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["id"] == str(booking.id)


def test_service_booking_list_as_non_owner(client, client_user, service, booking):
    client.force_authenticate(user=client_user)
    url = reverse('service-bookings-list', kwargs={'service_pk': service.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_service_booking_list_unauthenticated(client, service):
    url = reverse('service-bookings-list', kwargs={'service_pk': service.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_service_booking_list_invalid_service_id(client, provider):
    client.force_authenticate(user=provider)
    url = reverse('service-bookings-list', kwargs={'service_pk': "invalid"})
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND