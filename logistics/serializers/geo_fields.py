# logistics/serializers/geo_fields.py
"""Shared GeoJSON <-> GEOS serializer field for logistics serializers."""

from django.contrib.gis.geos import Point
from rest_framework import serializers


class PointJSONField(serializers.Field):
    """GeoJSON Point <-> GEOS Point."""

    def to_internal_value(self, data):
        if isinstance(data, Point):
            return data
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
