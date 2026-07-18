# search/serializers/business_search_serializer.py

from rest_framework import serializers

class BusinessSearchSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.EmailField()
    website = serializers.URLField()
    is_active = serializers.BooleanField()
    institution_id = serializers.CharField(allow_null=True, required=False)
    owner_id = serializers.IntegerField(allow_null=True, required=False)

    category = serializers.DictField()
    location = serializers.DictField()  # GeoPoint: {'lat': ..., 'lon': ...}