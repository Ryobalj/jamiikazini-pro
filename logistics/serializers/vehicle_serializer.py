# logistics/serializers/vehicle_serializers.py

from rest_framework import serializers
from logistics.models import Vehicle, Driver, TransportProvider
from logistics.choices import TransportTypeChoices
from logistics.models.vehicle import VerificationStatus
from logistics.models.vehicle_verification import VehicleVerification
from gov_integration.models.verification_request import VerificationRequest


class VerificationRequestStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationRequest
        fields = ['id', 'status', 'created_at', 'updated_at']
        # ref_name ya kipekee - inagongana na VerificationRequestStatusSerializer
        # ndani ya transport_provider_serializer.py
        ref_name = "VehicleVerificationRequestStatus"


class VehicleVerificationSerializer(serializers.ModelSerializer):
    tra_registration_verification = VerificationRequestStatusSerializer(read_only=True)
    latra_permit_verification = VerificationRequestStatusSerializer(read_only=True)

    class Meta:
        model = VehicleVerification
        fields = [
            "id", "tra_registration_verification", "latra_permit_verification",
            "overall_status", "notes", "created_at", "updated_at",
        ]
        read_only_fields = fields


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ["id", "full_name", "phone_number", "license_number", "license_photo", "profile_image"]
        # ref_name ya kipekee - inagongana na driver_serializer.DriverSerializer
        ref_name = "VehicleDriver"


class TransportProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportProvider
        fields = ["id", "user", "institution", "provider_type", "country_code", "is_approved"]
        # ref_name ya kipekee - vinginevyo inagongana na transport_provider_serializer
        # na shipment_serializer zenye TransportProviderSerializer kwenye drf_yasg schema
        ref_name = "VehicleTransportProvider"


class VehicleWriteSerializer(serializers.ModelSerializer):
    driver_ids = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), many=True, write_only=True, required=False
    )
    active_driver_id = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = Vehicle
        fields = [
            "id", "provider", "vehicle_type", "registration_number", "model_name",
            "capacity_kg", "volume_cbm", "image", "registration_photo",
            "latra_permit_number", "latra_permit_photo", "is_active",
            "driver_ids", "active_driver_id",
            "verification_statuses", "notes"
        ]
        read_only_fields = ["id", "provider"]

    def create(self, validated_data):
        drivers = validated_data.pop('driver_ids', [])
        active_driver = validated_data.pop('active_driver_id', None)
        vehicle = Vehicle.objects.create(**validated_data)
        if drivers:
            vehicle.drivers.set(drivers)
        if active_driver:
            vehicle.active_driver = active_driver
            vehicle.save()
        return vehicle

    def update(self, instance, validated_data):
        drivers = validated_data.pop('driver_ids', None)
        active_driver = validated_data.pop('active_driver_id', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if drivers is not None:
            instance.drivers.set(drivers)
        if active_driver:
            instance.active_driver = active_driver
        instance.save()
        return instance


class VehicleSerializer(serializers.ModelSerializer):
    provider = TransportProviderSerializer(read_only=True)
    drivers = DriverSerializer(many=True, read_only=True)
    active_driver = DriverSerializer(read_only=True)
    is_fully_verified = serializers.BooleanField(read_only=True)
    verification = VehicleVerificationSerializer(read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "provider",
            "vehicle_type",
            "registration_number",
            "model_name",
            "capacity_kg",
            "volume_cbm",
            "image",
            "registration_photo",
            "latra_permit_number",
            "latra_permit_photo",
            "is_active",
            "drivers",
            "active_driver",
            "verification_statuses",
            "is_fully_verified",
            "verification",
            "notes",
            "created_at",
            "updated_at",
        ]