# File: search/serializers/department_search_serializer.py

from rest_framework import serializers

class DepartmentSearchSerializer(serializers.Serializer):
    id = serializers.CharField()  # Department is UUID-keyed, not an integer PK
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    institution_id = serializers.CharField(allow_null=True, required=False)

    institution = serializers.DictField(required=False, allow_null=True)