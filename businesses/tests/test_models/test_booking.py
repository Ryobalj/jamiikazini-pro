# businesses/tests/test_models/test_booking.py

import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from businesses.models.booking import Booking, BookingLog, BookingStatus, PaymentStatus


@pytest.mark.django_db
def test_booking_creation(booking_factory, service_factory, user_factory):
    """Test booking creation and status fields."""
    service = service_factory(duration_minutes=30)
    client = user_factory(email="testuser@example.com")
    booking = booking_factory(service=service, client=client)

    assert booking.service == service
    assert booking.client == client
    assert booking.status == BookingStatus.PENDING
    assert booking.payment_status == PaymentStatus.PENDING


@pytest.mark.django_db
def test_estimated_end_time(booking_factory, service_factory, user_factory):
    """Test estimated_end_time property."""
    service = service_factory(duration_minutes=60)
    client = user_factory()
    scheduled_dt = timezone.now()
    booking = booking_factory(service=service, client=client, scheduled_datetime=scheduled_dt)

    assert booking.estimated_end_time == scheduled_dt + timedelta(minutes=60)


@pytest.mark.django_db
def test_save_valid_dates(booking_factory, service_factory, user_factory):
    """Test save method with valid actual times."""
    service = service_factory(duration_minutes=30)
    client = user_factory()
    booking = booking_factory(service=service, client=client)

    booking.actual_start_time = timezone.now()
    booking.actual_end_time = booking.actual_start_time + timedelta(minutes=30)

    booking.save()  # Should save successfully
    assert booking.pk is not None


@pytest.mark.django_db
def test_save_invalid_dates(booking_factory, service_factory, user_factory):
    """Test save method raises ValidationError when actual_end_time <= actual_start_time."""
    service = service_factory(duration_minutes=30)
    client = user_factory()
    booking = booking_factory(service=service, client=client)

    booking.actual_start_time = timezone.now()
    booking.actual_end_time = booking.actual_start_time
    with pytest.raises(ValidationError) as exc:
        booking.save()
    assert "Muda wa mwisho lazima uwe baada ya muda wa kuanza" in str(exc.value)


@pytest.mark.django_db
def test_booking_string_representation(booking_factory, service_factory, user_factory):
    """Test the __str__ method of Booking."""
    service = service_factory(duration_minutes=30, name="Massage Service")
    client = user_factory(full_name="john_doe")
    booking = booking_factory(service=service, client=client, status=BookingStatus.CONFIRMED)

    assert str(booking) == "Massage Service for john_doe (Confirmed)"


@pytest.mark.django_db
def test_bookinglog_creation(booking_factory):
    """Test BookingLog creation and auto-population of metadata."""
    booking = booking_factory()
    log = BookingLog.objects.create(booking=booking, action="CREATED", metadata=None)

    assert isinstance(log.metadata, dict)
    assert str(log) == f"{booking} - CREATED by System"


@pytest.mark.django_db
def test_bookinglog_metadata_auto_dict(booking_factory):
    """Test BookingLog metadata set to dict if not dict."""
    booking = booking_factory()
    log = BookingLog.objects.create(booking=booking, action="CONFIRMED", metadata="string_instead_of_dict")

    assert isinstance(log.metadata, dict)


@pytest.mark.django_db
def test_bookinglog_string_representation(booking_factory, user_factory):
    """Test __str__ method of BookingLog."""
    booking = booking_factory()
    user = user_factory()
    log = BookingLog.objects.create(booking=booking, action="CANCELLED")
    assert str(log) == f"{booking} - CANCELLED by System"

    # Now attach user
    log.user = user
    log.save()
    assert str(log) == f"{booking} - CANCELLED by System"