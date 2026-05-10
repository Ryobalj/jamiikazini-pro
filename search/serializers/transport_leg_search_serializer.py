# search/serializers/transport_leg_search_serializer.py

from rest_framework import serializers


class TransportLegSearchSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, help_text="Query ya ujumla (text search)")
    lat = serializers.FloatField(required=False, help_text="Latitude ya mtumiaji")
    lon = serializers.FloatField(required=False, help_text="Longitude ya mtumiaji")
    max_distance = serializers.FloatField(required=False, help_text="Umbali wa juu zaidi kwa km")
    page = serializers.IntegerField(default=1)
    per_page = serializers.IntegerField(default=10)