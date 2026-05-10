# kiini/serializers/institution_serializers.py

from rest_framework import serializers
from django.contrib.gis.geos import Point

from kiini.models.institution import Institution
from accounts.serializers import UserMinimalSerializer

class InstitutionSerializer(serializers.ModelSerializer):
    """
    Serializer ya Institution ikijumuisha lat/lon, owner, phone na tier/type display.
    """

    tier_name = serializers.CharField(source='tier.name', read_only=True)
    type_name = serializers.CharField(source='institution_type.name', read_only=True)

    owner = UserMinimalSerializer(read_only=True)

    location_lat = serializers.SerializerMethodField()
    location_lon = serializers.SerializerMethodField()

    lat = serializers.FloatField(write_only=True, required=False)
    lon = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = Institution
        fields = [
            "id", "name", "domain", "email", "phone", "address", "owner",
            "tier", "tier_name", "institution_type", "type_name",
            "lat", "lon", "location_lat", "location_lon",
            "is_active", "metadata", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "created_at", "updated_at", "tier_name", "type_name",
            "location_lat", "location_lon"
            # "owner" removed from read_only_fields so it can be set in perform_create
        ]

    def get_location_lat(self, obj):
        return obj.location.y if obj.location else None

    def get_location_lon(self, obj):
        return obj.location.x if obj.location else None

    def validate_domain(self, value):
        if not value:
            return value
        if " " in value:
            raise serializers.ValidationError("Domain must not contain spaces.")
        return value.lower().strip()

    def set_location_from_latlon(self, validated_data):
        lat = validated_data.pop("lat", None)
        lon = validated_data.pop("lon", None)
        if lat is not None and lon is not None:
            validated_data["location"] = Point(lon, lat)

    def create(self, validated_data):
        self.set_location_from_latlon(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self.set_location_from_latlon(validated_data)
        return super().update(instance, validated_data)