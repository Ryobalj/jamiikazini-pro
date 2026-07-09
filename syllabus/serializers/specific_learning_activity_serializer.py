# jamiikazini/syllabus/serializers/specific_learning_activity_serializer.py

from django.db.models import Max
from rest_framework import serializers
from syllabus.models.specific_learning_activity import SpecificLearningActivity


class SpecificLearningActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = SpecificLearningActivity
        fields = [
            "id",
            "learning_activity",
            "method",
            "name",
            "leading",
            "assessment_criteria",
            "teaching_aids",
            "references",
            "periods",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["order", "created_at", "updated_at"]

    # ----------------------------------
    # Internal helper
    # ----------------------------------
    def _val(self, data, field):
        if field in data:
            return data[field]
        if self.instance:
            return getattr(self.instance, field, None)
        return None

    # ----------------------------------
    # Field-level validations
    # ----------------------------------
    def validate_name(self, value):
        value = " ".join(value.strip().title().split())
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        return value

    def validate_method(self, value):
        value = " ".join(value.strip().title().split())
        if not value:
            raise serializers.ValidationError("Method cannot be empty.")
        return value

    def validate_leading(self, value):
        value = " ".join(value.strip().split())
        if not value:
            raise serializers.ValidationError("Leading action cannot be empty.")
        return value

    def validate_periods(self, value):
        if value <= 0:
            raise serializers.ValidationError("Periods must be at least 1.")
        return value

    # ----------------------------------
    # Object-level validation
    # ----------------------------------
    def validate(self, data):
        data = super().validate(data)

        name = self._val(data, "name")
        learning_activity = self._val(data, "learning_activity")

        if name and learning_activity:
            qs = SpecificLearningActivity.objects.filter(
                learning_activity=learning_activity,
                name__iexact=name,
            )
            if self.instance:
                qs = qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError(
                    {
                        "name": (
                            "A specific learning activity with this name "
                            "already exists under this learning activity."
                        )
                    }
                )

        # Clean optional text fields
        for field in ["assessment_criteria", "teaching_aids", "references"]:
            val = data.get(field)
            if isinstance(val, str):
                data[field] = val.strip()
            elif isinstance(val, list):
                data[field] = [str(v).strip() for v in val if str(v).strip()]

        return data

    # ----------------------------------
    # Create logic
    # ----------------------------------
    def create(self, validated_data):
        la = validated_data["learning_activity"]

        last_order = (
            SpecificLearningActivity.objects.filter(learning_activity=la)
            .aggregate(max_order=Max("order"))
            .get("max_order") or 0
        )

        validated_data["order"] = last_order + 1
        return super().create(validated_data)