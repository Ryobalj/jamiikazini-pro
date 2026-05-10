# businesses/tests/test_serializers/test_booking_serializer.py

import pytest
from django.utils import timezone
from datetime import timedelta
from businesses.models.booking import Booking, BookingLog
from businesses.serializers.booking_serializer import (
    BookingSerializer,
    BookingDetailSerializer,
    BookingStatusUpdateSerializer,
    BookingLogSerializer,
    BookingLogCreateSerializer
)
from rest_framework.test import APIRequestFactory


@pytest.mark.django_db
def test_booking_create_serializer_valid(user_factory, service_factory):
    factory = APIRequestFactory()
    request = factory.post('/fake-url/')  # au method yoyote, si lazima actual endpoint
    user = user_factory()
    request.user = user

    service = service_factory()

    data = {
        "client": user.id,
        "service": service.id,
        "scheduled_datetime": (timezone.now() + timedelta(days=1)).isoformat(),
        "notes": "Test booking creation"
    }

    serializer = BookingSerializer(data=data, context={'request': request})
    assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
def test_booking_create_serializer_invalid_past_date(booking_factory):
    booking = booking_factory()
    booking_data = {
        "client": booking.client.id,
        "service": booking.service.id,
        "scheduled_datetime": timezone.now() - timedelta(hours=1),
    }
    serializer = BookingSerializer(data=booking_data)
    assert not serializer.is_valid()
    assert "scheduled_datetime" in serializer.errors


@pytest.mark.django_db
def test_booking_detail_serializer_output(booking_factory):
    booking = booking_factory()
    serializer = BookingDetailSerializer(booking)
    data = serializer.data
    assert data["id"]
    assert "client" in data
    assert "service" in data
    assert "estimated_end_time" in data
    assert isinstance(data["estimated_end_time"], str)  # ISO format string


@pytest.mark.django_db
def test_booking_status_update_serializer_valid(booking_factory):
    booking = booking_factory()
    data = {"status": "CANCELLED", "cancellation_reason": "Nimeghairi kwa sababu binafsi"}
    serializer = BookingStatusUpdateSerializer(instance=booking, data=data)
    assert serializer.is_valid(), serializer.errors
    updated = serializer.save()
    assert updated.status == "CANCELLED"


@pytest.mark.django_db
def test_booking_status_update_serializer_invalid_without_reason(booking_factory):
    booking = booking_factory()
    data = {"status": "CANCELLED"}
    serializer = BookingStatusUpdateSerializer(instance=booking, data=data)
    assert not serializer.is_valid()
    assert "cancellation_reason" in serializer.errors


@pytest.mark.django_db
def test_booking_log_serializer_output(booking_factory, user_factory):
    booking = booking_factory()
    user = user_factory()
    log = BookingLog.objects.create(
        booking=booking,
        user=user,
        actor_type="CLIENT",
        action="CREATED",
        ip_address="127.0.0.1",
        user_agent="TestBrowser",
        metadata={"info": "Test"}
    )
    serializer = BookingLogSerializer(log)
    data = serializer.data
    assert data["id"]
    assert data["user"]["email"] == user.email
    assert data["actor_type"] == "CLIENT"
    assert data["action"] == "CREATED"


@pytest.mark.django_db
def test_booking_log_create_serializer_valid(booking_factory, user_factory):
    booking = booking_factory()
    user = user_factory()
    data = {
        "booking": booking.id,
        "user": user.id,
        "actor_type": "CLIENT",
        "action": "CREATED",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla",
        "metadata": {"key": "value"}
    }
    serializer = BookingLogCreateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()
    assert isinstance(instance, BookingLog)
    assert instance.actor_type == "CLIENT"