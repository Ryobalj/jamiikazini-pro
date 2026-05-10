# search/serializers/staff_profile_search_serializer.py

from rest_framework import serializers

class StaffProfileSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    position = serializers.CharField()
    title = serializers.CharField()
    phone = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    user = serializers.DictField(child=serializers.CharField())
    institution = serializers.DictField(child=serializers.CharField())
    department = serializers.DictField(child=serializers.CharField())

    institution_id = serializers.IntegerField()