# kiini/serializers/institution_tier_serializers.py

from rest_framework import serializers
from kiini.models.institution_tier import InstitutionTier


class InstitutionTierSerializer(serializers.ModelSerializer):
    name_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InstitutionTier
        fields = [
            "id",
            "name",
            "name_display",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "name_display"]

    def get_name_display(self, obj):
        return obj.get_name_display()