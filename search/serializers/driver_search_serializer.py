# File: search/serializers/driver_search_serializer.py

from rest_framework import serializers


class DriverSearchSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, help_text="Tafuta kwa jina au namba ya leseni")
    provider_id = serializers.CharField(required=False, help_text="Chuja kwa transport_provider_id")
    page = serializers.IntegerField(default=1)
    per_page = serializers.IntegerField(default=10)