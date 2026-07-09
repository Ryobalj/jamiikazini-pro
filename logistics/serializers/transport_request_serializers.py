# logistics/serializers/transport_request_serializers.py
#
# Rewritten against the current TransportRequest model (requestor_type/business/
# institution, package_description, weight_kg, PointField pickup/dropoff,
# address texts). The previous version referenced a long-gone model shape
# (Location FKs, preferred_vehicle_type, cargo_weight_kg...) and raised
# ImproperlyConfigured on every request.

from django.contrib.gis.geos import Point
from rest_framework import serializers
from logistics.models import TransportRequest, Vehicle


class PointJSONField(serializers.Field):
    """GeoJSON Point <-> GEOS Point."""

    def to_internal_value(self, data):
        try:
            if isinstance(data, dict) and "coordinates" in data:
                lon, lat = data["coordinates"]
                return Point(float(lon), float(lat), srid=4326)
        except (TypeError, ValueError, IndexError):
            pass
        raise serializers.ValidationError(
            'Expected GeoJSON Point: {"type": "Point", "coordinates": [lon, lat]}'
        )

    def to_representation(self, value):
        if value is None:
            return None
        return {"type": "Point", "coordinates": [value.x, value.y]}


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


class TransportRequestSerializer(serializers.ModelSerializer):
    pickup_location = PointJSONField(read_only=True)
    dropoff_location = PointJSONField(read_only=True)

    class Meta:
        model = TransportRequest
        fields = [
            "id",
            "requestor_type",
            "business",
            "institution",
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
            "requested_at",
            "expires_at",
        ]
        read_only_fields = fields


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
