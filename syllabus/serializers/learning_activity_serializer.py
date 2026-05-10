# jamiikazini/syllabus/serializers/learning_activity_serializer.py

from rest_framework import serializers
from syllabus.models.learning_activity import LearningActivity


class LearningActivitySerializer(serializers.ModelSerializer):
    # 🔥 ADD THESE READ-ONLY FIELDS FOR FRONTEND
    specific_competence_name = serializers.CharField(
        source="specific_competence.name", 
        read_only=True
    )
    main_competence_name = serializers.CharField(
        source="specific_competence.main_competence.name", 
        read_only=True
    )
    subject_version_id = serializers.UUIDField(
        source="specific_competence.main_competence.subject_version.id", 
        read_only=True
    )
    subject_version_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LearningActivity
        fields = [
            "id",
            "specific_competence",
            "name",
            "order",
            "created_at",
            "updated_at",
            # 🔥 New read-only fields
            "specific_competence_name",
            "main_competence_name", 
            "subject_version_id",
            "subject_version_display"
        ]
        read_only_fields = ["order", "created_at", "updated_at"]

    def get_subject_version_display(self, obj):
        sv = obj.specific_competence.main_competence.subject_version
        return f"{sv.subject.name} ({sv.class_level.name}) - {sv.syllabus_version.year}"

    # ------------------------------------------------
    # INTERNAL HELPER: Retrieve new or existing value
    # ------------------------------------------------
    def _value(self, data, field):
        """
        Returns either the new value (if provided)
        or the instance value (on update).
        """
        return data.get(field) if field in data else getattr(self.instance, field, None)

    # ------------------------------------------------
    # NAME VALIDATION + NORMALIZATION
    # ------------------------------------------------
    def validate_name(self, value):
        """
        Clean whitespace, ensure not empty, normalize formatting.
        """
        if not isinstance(value, str):
            raise serializers.ValidationError("Name must be a string.")

        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Jina la activity halinaweza kuwa tupu.")

        # 👉 Unichague:
        # normalized = cleaned.title()       # Kama unataka Title Case
        # normalized = cleaned.lower()       # Kama unataka lower-case normalization
        normalized = cleaned

        return normalized

    # ------------------------------------------------
    # GLOBAL VALIDATION
    # ------------------------------------------------
    def validate(self, data):
        data = super().validate(data)

        specific_competence = self._value(data, "specific_competence")
        name = self._value(data, "name")

        # Only run validation if both fields are available
        if specific_competence and name:
            qs = LearningActivity.objects.filter(
                specific_competence=specific_competence,
                name__iexact=name,
            )

            # Exclude self on update
            if self.instance:
                qs = qs.exclude(id=self.instance.id)

            if qs.exists():
                raise serializers.ValidationError({
                    "name": f"Learning activity '{name}' tayari ipo kwa competence hii."
                })

        return data

    # ------------------------------------------------
    # OPTIONAL AUTO-ORDER (enable if you need it)
    # ------------------------------------------------
    def create(self, validated_data):
        """
        Automatically assign next order number if the model uses ordering.
        """
        if "order" not in validated_data:
            last = LearningActivity.objects.order_by("-order").first()
            validated_data["order"] = (last.order + 1) if last else 1

        return super().create(validated_data)