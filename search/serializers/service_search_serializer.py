# search/serializers/service_search_serializer.py

from rest_framework import serializers


class BusinessSerializer(serializers.Serializer):
    # required=False throughout: when the underlying FK is unset (e.g. a
    # Service with no category), django_elasticsearch_dsl's automatic
    # ObjectField resolution yields an empty object rather than None.
    id = serializers.CharField(required=False, allow_null=True)  # Business is UUID-keyed, not an integer PK
    name = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    is_active = serializers.BooleanField(required=False, allow_null=True)

    class Meta:
        # ref_name ya kipekee - inagongana na businesses.BusinessSerializer kwenye schema
        ref_name = "ServiceSearchBusiness"


class CategorySerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True)  # BusinessCategory is UUID-keyed, not an integer PK
    name = serializers.CharField(required=False, allow_null=True)
    slug = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class ServiceSearchSerializer(serializers.Serializer):
    id = serializers.CharField()  # Service is UUID-keyed, not an integer PK
    name = serializers.CharField()
    description = serializers.CharField()
    price = serializers.FloatField()
    billing_type = serializers.CharField()
    location_type = serializers.CharField()
    requires_booking = serializers.BooleanField()
    is_available = serializers.BooleanField()
    duration_minutes = serializers.IntegerField(required=False, allow_null=True)
    created_at = serializers.DateTimeField()

    business = BusinessSerializer(required=False, allow_null=True)
    category = CategorySerializer(required=False, allow_null=True)
    location = serializers.DictField(required=False, allow_null=True)  # {'lat': ..., 'lon': ...}

    distance = serializers.SerializerMethodField()

    def get_distance(self, obj):
        return obj.meta.get("sort", [None])[0] if obj.meta.get("sort") else None