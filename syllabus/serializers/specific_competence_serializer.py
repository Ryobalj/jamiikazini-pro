# jamiikazini/syllabus/serializers/specific_competence_serializer.py

from rest_framework import serializers
from django.db.models import Max
from syllabus.models.specific_competence import SpecificCompetence


class SpecificCompetenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = SpecificCompetence
        fields = [
            "id",
            "main_competence",
            "name",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["order", "created_at", "updated_at"]

    def _val(self, data, field):
        """
        Helper to get value from data or instance for validation
        """
        return data.get(field) if field in data else getattr(self.instance, field, None)

    def validate_name(self, value):
        # Trim and normalize name
        value = " ".join(value.strip().title().split())
        if not value:
            raise serializers.ValidationError(
                "Name of specific competence cannot be empty."
            )
        return value

    def validate(self, data):
        data = super().validate(data)
        main_competence = self._val(data, "main_competence")
        name = self._val(data, "name")

        if main_competence and name:
            qs = SpecificCompetence.objects.filter(
                main_competence=main_competence,
                name__iexact=name.strip()
            )
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError(
                    "This specific competence already exists under the selected main competence."
                )

        return data

    def create(self, validated_data):
        """
        Auto-assign order per main_competence
        """
        main_comp = validated_data["main_competence"]
        last_order = (
            SpecificCompetence.objects.filter(main_competence=main_comp)
            .aggregate(Max("order"))
            .get("order__max") or 0
        )
        validated_data["order"] = last_order + 1
        return super().create(validated_data)