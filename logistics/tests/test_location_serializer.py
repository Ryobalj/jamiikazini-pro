# logistics/tests/test_location_serializer.py

import pytest
from logistics.models import Location
from logistics.serializers.location_serializer import LocationSerializer
from decimal import Decimal


@pytest.mark.django_db
class TestLocationSerializer:

    def test_create_location_successfully(self):
        data = {
            "name": "Test Location",
            "address": "123 Test Street",
            "latitude": "6.5244",
            "longitude": "3.3792",
            "description": "Test description",
        }
        serializer = LocationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        location = serializer.save()

        assert location.name == "Test Location"
        assert location.latitude == Decimal("6.5244")
        assert location.longitude == Decimal("3.3792")

    def test_latitude_validation(self):
        data = {
            "name": "Invalid Latitude",
            "latitude": "200.0",  # invalid
            "longitude": "30.0",
        }
        serializer = LocationSerializer(data=data)
        assert not serializer.is_valid()
        assert "latitude" in serializer.errors

    def test_longitude_validation(self):
        data = {
            "name": "Invalid Longitude",
            "latitude": "5.0",
            "longitude": "-200.0",  # invalid
        }
        serializer = LocationSerializer(data=data)
        assert not serializer.is_valid()
        assert "longitude" in serializer.errors

    def test_update_location_with_gps(self):
        location = Location.objects.create(
            name="Old Location",
            latitude="0.0000",
            longitude="0.0000"
        )

        data = {
            "latitude": "10.123456",
            "longitude": "20.654321",
        }
        serializer = LocationSerializer(instance=location, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()

        assert updated.latitude == Decimal("10.123456")
        assert updated.longitude == Decimal("20.654321")

    def test_read_only_fields_cannot_be_updated(self):
        location = Location.objects.create(
            name="ReadOnly Location",
            latitude="0.0",
            longitude="0.0"
        )

        data = {
            "created_at": "2020-01-01T00:00:00Z",  # should be ignored
            "updated_at": "2020-01-01T00:00:00Z",  # should be ignored
        }

        serializer = LocationSerializer(instance=location, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()

        assert updated.created_at != "2020-01-01T00:00:00Z"
        assert updated.updated_at != "2020-01-01T00:00:00Z"
