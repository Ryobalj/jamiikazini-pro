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
def branch(business):
    from businesses.models.branch import Branch
    from django.contrib.gis.geos import Point
    return Branch.objects.create(name="Main Branch", business=business, location=Point(39.28, -6.81))


@pytest.fixture
def booking(service, client_user):
    return Booking.objects.create(
        service=service,
        client=client_user,
        scheduled_datetime="2025-07-02T10:00:00Z",
        notes="My laptop wonâ€™t start",
        status="PENDING"
    )


def test_service_list_view(client, business):
    url = reverse('businesses:business-services-list', kwargs={'business_pk': business.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_service_detail_view(client, service, business):
    url = reverse('businesses:business-services-detail', kwargs={'business_pk': service.business.pk, 'pk': service.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == str(service.id)


def test_nested_service_booking_view_as_owner(client, provider, service, booking, business, branch):
    client.force_authenticate(user=provider)
    url = reverse('businesses:service-bookings-list', kwargs={'business_pk': business.pk, 'branch_pk': branch.pk, 'service_pk': service.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
    assert str(booking.id) in [str(b["id"]) for b in data]


def test_nested_service_booking_view_as_other_user(client, client_user, service, business, branch):
    client.force_authenticate(user=client_user)
    url = reverse('businesses:service-bookings-list', kwargs={'business_pk': business.pk, 'branch_pk': branch.pk, 'service_pk': service.pk})
    response = client.get(url)
    # isolation ni kwa filter: orodha tupu
    assert response.status_code == status.HTTP_200_OK


def test_nested_service_booking_view_unauthenticated(client, service, business, branch):
    url = reverse('businesses:service-bookings-list', kwargs={'business_pk': business.pk, 'branch_pk': branch.pk, 'service_pk': service.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED