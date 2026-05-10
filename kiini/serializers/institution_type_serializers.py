# kiini/serializers/institution_type_serializers.py

from rest_framework import serializers
from kiini.models.institution_type import InstitutionType


class InstitutionTypeSerializer(serializers.ModelSerializer):
    name = serializers.ChoiceField(
        choices=InstitutionType.TypeChoices.choices
    )
    name_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InstitutionType
        fields = [
            "id",
            "name",             # raw value like 'NGO'
            "name_display",     # human-readable like 'Non-Governmental Organization'
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "name_display"]

    def get_name_display(self, obj):
        return obj.get_name_display()