# jamiikazini/syllabus/serializers/syllabus_version_serializer.py

from rest_framework import serializers
from syllabus.models.syllabus_version import SyllabusVersion


class SyllabusVersionSerializer(serializers.ModelSerializer):
    """
    PROMAX Serializer:
    - Enforces valid year
    - Relies on model to clear previous current version
    - Adds human-readable display
    """

    display = serializers.SerializerMethodField()

    class Meta:
        model = SyllabusVersion
        fields = [
            "id",
            "year",
            "evaluation_aid",
            "is_current",
            "display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_year(self, value):
        if value < 1900 or value > 2100:
            raise serializers.ValidationError("Invalid year range.")
        return value

    def get_display(self, obj):
        return f"Syllabus {obj.year}{' (current)' if obj.is_current else ''}"