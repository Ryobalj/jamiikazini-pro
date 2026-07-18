# search/serializers/staff_profile_search_serializer.py

from rest_framework import serializers

class StaffProfileSearchSerializer(serializers.Serializer):
    id = serializers.CharField()  # StaffProfile is UUID-keyed, not an integer PK
    position = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    title = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    user = serializers.DictField(required=False, allow_null=True)
    institution = serializers.DictField(required=False, allow_null=True)
    department = serializers.DictField(required=False, allow_null=True)

    institution_id = serializers.CharField(allow_null=True, required=False)