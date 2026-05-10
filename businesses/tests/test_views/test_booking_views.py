import pytest
from rest_framework import status
from django.urls import reverse
from businesses.serializers.booking_serializer import (
  BookingDetailSerializer,
  BookingLogSerializer,
  BookingLogCreateSerializer
  )
from django.utils import timezone
from datetime import timedelta
from businesses.models.booking import Booking, BookingLog
from rest_framework.test import APIRequestFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def booking(client_user, service_factory, booking_factory):
    service = service_factory(duration_minutes=45)
    return booking_factory(client=client_user, service=service)


@pytest.fixture
def auth_client(api_client, client_user):
    api_client.force_authenticate(user=client_user)
    return api_client


def test_create_booking(auth_client, service_factory, client_user):
    service = service_factory()
    url = reverse("businesses:booking-list")  # this must be correct URL for POST
    data = {
        "client": client_user.id,
        "service": service.id,
        "scheduled_datetime": (timezone.now() + timedelta(days=1)).isoformat(),
        "notes": "Tafadhali fika kwa wakati"
    }
    response = auth_client.post(url, data, format='json')  # ensure format json
    assert response.status_code == status.HTTP_201_CREATED
    assert Booking.objects.filter(client=client_user, service=service).exists()


def test_retrieve_booking(auth_client, booking):
    url = reverse("businesses:booking-detail", args=[booking.id])
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(booking.id)
    assert "estimated_end_time" in response.data


def test_update_status(auth_client, booking):
    url = reverse("businesses:booking-update-status", args=[booking.id])
    data = {"status": "CANCELLED", "cancellation_reason": "Change of plans"}
    response = auth_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK
    booking.refresh_from_db()
    assert booking.status == "CANCELLED"
    assert BookingLog.objects.filter(booking=booking, action__icontains="STATUS_CHANGED").exists()


def test_logs_action(auth_client, booking):
    log_url = reverse("businesses:booking-logs", args=[booking.id])
    response = auth_client.get(log_url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_permission_required(api_client, booking):
    """
    Hakuna authentication - inapaswa kurudisha 401 Unauthorized
    """
    url = reverse("businesses:booking-detail", args=[booking.id])
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_forbidden_access_for_non_owner(api_client, booking_factory, user_factory):
    booking_owner = user_factory()
    other_user = user_factory()
    booking = booking_factory(client=booking_owner)

    api_client.force_authenticate(user=other_user)
    url = reverse("businesses:booking-detail", args=[booking.id])
    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_invalid_datetime(auth_client, service_factory):
    service = service_factory()
    url = reverse("businesses:booking-list")
    data = {
        "service": service.id,
        "scheduled_datetime": (timezone.now() - timedelta(days=1)).isoformat(),
        "notes": "Late"
    }
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "scheduled_datetime" in response.data


@pytest.mark.django_db
def test_booking_log_list(api_client, booking_log_factory, client_user):
    log = booking_log_factory()
    api_client.force_authenticate(user=client_user)

    url = reverse("businesses:booking-log-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert any(item["id"] == str(log.id) for item in response.data)


@pytest.mark.django_db
def test_booking_log_create_serializer_valid(booking_factory, client_user):
    booking = booking_factory(client=client_user)
    payload = {
        "booking": booking.id,
        "actor_type": "CLIENT",
        "action": "CREATED",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "metadata": {"info": "Just testing"},
    }

    # Fake request with authenticated user in context
    factory = APIRequestFactory()
    request = factory.post("/fake-url/", payload, format="json")
    request.user = client_user

    serializer = BookingLogCreateSerializer(data=payload, context={"request": request})
    assert serializer.is_valid(), serializer.errors

    log = serializer.save()

    assert isinstance(log, BookingLog)
    assert log.user == client_user
    assert log.booking == booking
    assert log.action == "CREATED"


@pytest.mark.django_db
def test_booking_log_retrieve(api_client, booking_log_factory, client_user):
    log = booking_log_factory()
    api_client.force_authenticate(user=client_user)

    url = reverse("businesses:booking-log-detail", args=[log.id])
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(log.id)


@pytest.mark.django_db
def test_booking_log_update(api_client, booking_log_factory, client_user):
    log = booking_log_factory(action="CREATED")
    api_client.force_authenticate(user=client_user)

    payload = {"action": "UPDATED"}
    url = reverse("businesses:booking-log-detail", args=[log.id])
    response = api_client.patch(url, data=payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    log.refresh_from_db()
    assert log.action == "UPDATED"


@pytest.mark.django_db
def test_booking_log_delete(api_client, booking_log_factory, client_user):
    log = booking_log_factory()
    api_client.force_authenticate(user=client_user)

    url = reverse("businesses:booking-log-detail", args=[log.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not BookingLog.objects.filter(id=log.id).exists()
