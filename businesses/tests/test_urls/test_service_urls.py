import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.gis.geos import Point

from accounts.models import User
from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from businesses.models.service import Service
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
        name="PC Repair",
        business=business,
        description="Fixing PCs and laptops",
        price=50.00
    )


@pytest.fixture
def booking(service, client_user):
    return Booking.objects.create(
        service=service,
        client=client_user,
        scheduled_datetime="2025-07-02T10:00:00Z",
        notes="My laptop won’t start",
        status="PENDING"
    )


def test_service_list_view(client):
    url = reverse('service-list')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_service_detail_view(client, service):
    url = reverse('service-detail', kwargs={'pk': service.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == str(service.id)


def test_nested_service_booking_view_as_owner(client, provider, service, booking):
    client.force_authenticate(user=provider)
    url = reverse('service-booking-list', kwargs={'service_pk': service.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert str(booking.id) in [str(b["id"]) for b in response.data["results"]]


def test_nested_service_booking_view_as_other_user(client, client_user, service):
    client.force_authenticate(user=client_user)
    url = reverse('service-booking-list', kwargs={'service_pk': service.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_nested_service_booking_view_unauthenticated(client, service):
    url = reverse('service-booking-list', kwargs={'service_pk': service.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED