# File: search/serializers/branch_search_serializer.py
# Maelezo: Serializer ya BranchDocument kwa ajili ya kuwasilisha data kutoka Elasticsearch

from rest_framework import serializers
from search.documents.branch_document import BranchDocument

class BranchSearchSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.EmailField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    
    business = serializers.DictField()
    services = serializers.ListField(child=serializers.DictField())
    location = serializers.DictField()  # GeoPoint represented as {'lat': ..., 'lon': ...}