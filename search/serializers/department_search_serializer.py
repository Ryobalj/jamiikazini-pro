# File: search/serializers/department_search_serializer.py

from rest_framework import serializers

class DepartmentSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    institution_id = serializers.IntegerField()

    institution = serializers.DictField()