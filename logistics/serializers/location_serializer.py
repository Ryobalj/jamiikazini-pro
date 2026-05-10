# logistics/serializers/location_serializer.py

from rest_framework import serializers
from logistics.models import Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "address",
            "latitude",
            "longitude",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_latitude(self, value):
        if not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if not (-180 <= value <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value

    def update(self, instance, validated_data):
        """
        Automatically updates latitude and longitude if provided.
        """
        latitude = validated_data.get("latitude")
        longitude = validated_data.get("longitude")

        if latitude is not None and longitude is not None:
            instance.update_from_gps(latitude, longitude)
            validated_data.pop("latitude")
            validated_data.pop("longitude")

        # Update other fields normally
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance