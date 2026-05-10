# jamiikazini/syllabus/serializers/subject_version_serializer.py

from rest_framework import serializers
from syllabus.models import SubjectVersion


class SubjectVersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubjectVersion
        fields = [
            "id",
            "syllabus_version",
            "subject",
            "class_level",
            "is_english",
            "is_awali",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["order", "created_at", "updated_at"]

    # ----------------------------------------------------
    # MAIN VALIDATION (handles both create & update)
    # ----------------------------------------------------
    def validate(self, attrs):
        """
        Unique combination:
        syllabus_version + subject + class_level
        """
        # Get instance values (UPDATE)
        instance = getattr(self, "instance", None)

        syllabus_version = attrs.get("syllabus_version") or (instance.syllabus_version if instance else None)
        subject = attrs.get("subject") or (instance.subject if instance else None)
        class_level = attrs.get("class_level") or (instance.class_level if instance else None)

        # Only validate when all fields available
        if syllabus_version and subject and class_level:
            qs = SubjectVersion.objects.filter(
                syllabus_version=syllabus_version,
                subject=subject,
                class_level=class_level,
            )
            if instance:
                qs = qs.exclude(pk=instance.pk)

            if qs.exists():
                raise serializers.ValidationError({
                    "class_level": "This combination of syllabus_version, subject and class_level already exists."
                })

        return attrs

    # ----------------------------------------------------
    # OPTIONAL: Let DRF handle boolean conversion
    # ----------------------------------------------------
    def to_internal_value(self, data):
        """
        Convert strings 'true'/'false' to real booleans automatically.
        """
        if "is_english" in data:
            data["is_english"] = data["is_english"] in [True, "true", "True", 1, "1"]

        if "is_awali" in data:
            data["is_awali"] = data["is_awali"] in [True, "true", "True", 1, "1"]

        return super().to_internal_value(data)