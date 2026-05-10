# jamiikazini/syllabus/serializers/class_level_serializer.py

from rest_framework import serializers
from syllabus.models.class_level import ClassLevel


class ClassLevelSerializer(serializers.ModelSerializer):
    """
    PRO VERSION:
    - Ensures class name uniqueness (case-insensitive)
    - Normalizes names to Title Case
    - Auto-assigns proper ordering (ascending sequence)
    - Prevents accidental order modification on update
    """

    class Meta:
        model = ClassLevel
        fields = [
            "id",
            "name",
            "description",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "order", "created_at", "updated_at")

    # ------------------------------------------------
    # NAME VALIDATION + NORMALIZATION
    # ------------------------------------------------
    def validate_name(self, value):
        """Normalize name and enforce uniqueness."""
        if not isinstance(value, str):
            raise serializers.ValidationError("Name must be a string.")

        normalized = value.strip().title()

        qs = ClassLevel.objects.filter(name__iexact=normalized)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("Darasa hili tayari limesajiliwa.")

        return normalized

    # ------------------------------------------------
    # GLOBAL VALIDATION
    # ------------------------------------------------
    def validate(self, data):
        """Extra validation (currently none, but kept for future scaling)."""
        data = super().validate(data)
        return data

    # ------------------------------------------------
    # AUTO SET ORDER ON CREATE
    # ------------------------------------------------
    def create(self, validated_data):
        """
        Automatically assign the next order number if not provided.
        Order only increments: 1, 2, 3, ...
        """
        if not validated_data.get("order"):
            last_level = ClassLevel.objects.order_by("-order").first()
            validated_data["order"] = (last_level.order + 1) if last_level else 1

        return super().create(validated_data)

    # ------------------------------------------------
    # UPDATE: Prevent order override unless intentional
    # ------------------------------------------------
    def update(self, instance, validated_data):
        """
        By default, prevent order modification during updates.
        To change order, developer must override logic explicitly.
        """
        validated_data.pop("order", None)
        return super().update(instance, validated_data)