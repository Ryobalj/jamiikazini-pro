# search/serializers/service_search_serializer.py

from rest_framework import serializers


class BusinessSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    is_active = serializers.BooleanField()


class CategorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField()


class ServiceSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    price = serializers.FloatField()
    billing_type = serializers.CharField()
    location_type = serializers.CharField()
    requires_booking = serializers.BooleanField()
    is_available = serializers.BooleanField()
    duration_minutes = serializers.IntegerField()
    created = serializers.DateTimeField()

    business = BusinessSerializer()
    category = CategorySerializer()
    location = serializers.DictField()  # {'lat': ..., 'lon': ...}

    distance = serializers.SerializerMethodField()

    def get_distance(self, obj):
        return obj.meta.get("sort", [None])[0] if obj.meta.get("sort") else None