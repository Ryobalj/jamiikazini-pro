import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from django.contrib.gis.geos import Point
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from kiini.models.institution import Institution
from businesses.models import Business, Service, Booking

pytestmark = pytest.mark.django_db


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.fixture
def setup_booking():
    institution = Institution.objects.create(name="Institution X", domain="x.jamiikazini.com")
    
    owner = User.objects.create_user(email="owner@example.com", password="pass123", institution=institution)
    client_user = User.objects.create_user(email="client@example.com", password="pass123", institution=institution)

    business = Business.objects.create(name="Test Biz", owner=owner, institution=institution, location=Point(39.2, -6.8))
    service = Service.objects.create(name="Test Service", business=business)

    booking = Booking.objects.create(
        client=client_user,
        service=service,
        scheduled_datetime=timezone.now() + timedelta(days=1),
        notes="Test",
    )

    return {
        "owner": owner,
        "client_user": client_user,
        "service": service,
        "booking": booking,
    }


def test_service_booking_list_success(setup_booking):
    owner = setup_booking["owner"]
    service = setup_booking["service"]

    client = auth_client(owner)
    url = reverse("businesses:service-booking-list", kwargs={"service_pk": service.id})
    response = client.get(url)

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["service"] == service.id


def test_service_booking_list_unauthenticated(setup_booking):
    service = setup_booking["service"]
    url = reverse("businesses:service-booking-list", kwargs={"service_pk": service.id})
    client = APIClient()
    response = client.get(url)

    assert response.status_code == 401


def test_service_booking_list_forbidden_for_non_owner(setup_booking):
    client_user = setup_booking["client_user"]
    service = setup_booking["service"]

    client = auth_client(client_user)
    url = reverse("businesses:service-booking-list", kwargs={"service_pk": service.id})
    response = client.get(url)

    assert response.status_code == 403


def test_service_booking_invalid_service_pk(setup_booking):
    owner = setup_booking["owner"]
    client = auth_client(owner)

    url = reverse("businesses:service-booking-list", kwargs={"service_pk": 999})  # Service haipo
    response = client.get(url)

    # Kutegemea implementation yako, inaweza kuwa 404 (not found) au 200 (empty list)
    assert response.status_code in [200, 403, 404]