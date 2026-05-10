# search/serializers/transport_provider_search_serializer.py

from rest_framework import serializers


class TransportProviderSearchSerializer(serializers.Serializer):
    """
    Serializer for transport provider search filters.
    """
    q = serializers.CharField(required=False, help_text="Search keyword for username or email")
    lat = serializers.FloatField(required=False, help_text="Latitude for location-based search")
    lon = serializers.FloatField(required=False, help_text="Longitude for location-based search")
    max_distance = serializers.IntegerField(required=False, help_text="Max distance in km")
    page = serializers.IntegerField(required=False, default=1)
    per_page = serializers.IntegerField(required=False, default=10)