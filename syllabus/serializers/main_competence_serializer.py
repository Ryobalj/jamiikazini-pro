# jamiikazini/syllabus/serializers/main_competence_serializer.py

from rest_framework import serializers
from syllabus.models.main_competence import MainCompetence

class MainCompetenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainCompetence
        fields = [
            "id",
            "subject_version",
            "name",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["order", "created_at", "updated_at"]

    # ------------------------------------------------
    # HELPER
    # ------------------------------------------------
    def _val(self, data, field):
        return data.get(field) if field in data else getattr(self.instance, field, None)

    # ------------------------------------------------
    # NAME VALIDATION
    # ------------------------------------------------
    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name of the competence cannot be empty.")
        # Optional: normalize title case
        return " ".join(value.title().split())

    # ------------------------------------------------
    # GLOBAL VALIDATION
    # ------------------------------------------------
    def validate(self, data):
        data = super().validate(data)

        subject_version = self._val(data, "subject_version")
        name = self._val(data, "name")

        if subject_version and name:
            qs = MainCompetence.objects.filter(
                subject_version=subject_version,
                name__iexact=name
            )
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError(
                    {"name": "This main competence already exists for the selected subject version."}
                )

        return data

    # ------------------------------------------------
    # AUTO-ORDERING (optional)
    # ------------------------------------------------
    def create(self, validated_data):
        if not validated_data.get("order"):
            last = MainCompetence.objects.filter(
                subject_version=validated_data["subject_version"]
            ).order_by("-order").first()
            validated_data["order"] = (last.order + 1) if last else 1
        return super().create(validated_data)