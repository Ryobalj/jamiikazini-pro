# logistics/serializers/transport_request_serializers.py
#
# Rewritten against the current TransportRequest model (requestor_type/business/
# institution, package_description, weight_kg, PointField pickup/dropoff,
# address texts). The previous version referenced a long-gone model shape
# (Location FKs, preferred_vehicle_type, cargo_weight_kg...) and raised
# ImproperlyConfigured on every request.

from rest_framework import serializers
from logistics.models import TransportRequest, Vehicle
from logistics.serializers.geo_fields import PointJSONField


class TransportRequestWriteSerializer(serializers.ModelSerializer):
    pickup_location = PointJSONField()
    dropoff_location = PointJSONField()
    suggested_transport_type = serializers.ChoiceField(
        choices=TransportRequest._meta.get_field("suggested_transport_type").choices,
        required=False,
    )

    def create(self, validated_data):
        if not validated_data.get("suggested_transport_type"):
            temp = TransportRequest(**validated_data)
            try:
                validated_data["suggested_transport_type"] = temp.suggest_transport_type()
            except Exception:
                validated_data["suggested_transport_type"] = "boda_boda"
        return super().create(validated_data)

    class Meta:
        model = TransportRequest
        fields = [
            "id",
            "package_description",
            "weight_kg",
            "volume_cbm",
            "estimated_value",
            "suggested_transport_type",
            "pickup_location",
            "dropoff_location",
            "pickup_address_text",
            "dropoff_address_text",
            "origin_country",
            "destination_country",
            "expires_at",
        ]
        read_only_fields = ["id"]


class TransportRequestAssignmentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    assignment_status = serializers.CharField()
    agreed_fare = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    client_confirmed_at = serializers.DateTimeField(allow_null=True)
    vehicle = serializers.CharField(source="vehicle.registration_number", default=None)
    provider_name = serializers.CharField(source="assigned_to.user.full_name", default=None)
    current_location = PointJSONField(read_only=True, default=None)


class TransportRequestSerializer(serializers.ModelSerializer):
    pickup_location = PointJSONField(read_only=True)
    dropoff_location = PointJSONField(read_only=True)
    assignment = serializers.SerializerMethodField()

    class Meta:
        model = TransportRequest
        fields = [
            "id",
            "requestor_type",
            "business",
            "institution",
            "requested_by",
            "package_description",
            "weight_kg",
            "volume_cbm",
            "estimated_value",
            "suggested_transport_type",
            "pickup_location",
            "dropoff_location",
            "pickup_address_text",
            "dropoff_address_text",
            "origin_country",
            "destination_country",
            "status",
            "is_accepted",
            "order",
            "estimated_fare",
            "requested_at",
            "expires_at",
            "assignment",
        ]
        read_only_fields = fields

    def get_assignment(self, obj):
        assignment = getattr(obj, "transportassignment", None)
        if assignment is None:
            return None
        return TransportRequestAssignmentSerializer(assignment).data


class RecommendedVehicleSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id", "vehicle_type", "registration_number",
            "capacity_kg", "volume_cbm",
            "distance_km"
        ]

    def get_distance_km(self, obj):
        return round(obj.distance.km, 2) if hasattr(obj, "distance") else None
