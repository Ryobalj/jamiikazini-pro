# logistics/serializers/transport_request_serializers.py

from rest_framework import serializers
from logistics.models import TransportRequest, Location, Vehicle
from logistics.serializers.location_serializer import LocationSerializer  # ensure this exists
from logistics.serializers.vehicle_serializer import VehicleSerializer
from logistics.models.vehicle import VerificationStatus


class TransportRequestWriteSerializer(serializers.ModelSerializer):
    pickup_location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), write_only=True, required=True
    )
    delivery_location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), write_only=True, required=True
    )

    class Meta:
        model = TransportRequest
        fields = [
            "id",
            "pickup_location_id",
            "delivery_location_id",
            "preferred_vehicle_type",
            "pickup_datetime",
            "cargo_weight_kg",
            "cargo_volume_cbm",
            "description",
            "contact_person",
            "contact_phone",
            "is_active",
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TransportRequestSerializer(serializers.ModelSerializer):
    pickup_location = LocationSerializer(read_only=True)
    delivery_location = LocationSerializer(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    assigned_vehicle = VehicleSerializer(read_only=True)
    is_fulfilled = serializers.BooleanField(read_only=True)

    class Meta:
        model = TransportRequest
        fields = [
            "id",
            "pickup_location",
            "delivery_location",
            "preferred_vehicle_type",
            "pickup_datetime",
            "cargo_weight_kg",
            "cargo_volume_cbm",
            "description",
            "contact_person",
            "contact_phone",
            "is_active",
            "is_fulfilled",
            "assigned_vehicle",
            "created_by",
            "created_at",
            "updated_at",
        ]


class RecommendedVehicleSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id", "vehicle_type", "plate_number",
            "capacity_kg", "volume_cbm",
            "distance_km"
        ]

    def get_distance_km(self, obj):
        return round(obj.distance.km, 2) if hasattr(obj, "distance") else None
