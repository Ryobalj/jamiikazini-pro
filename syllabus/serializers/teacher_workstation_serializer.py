# jamiikazini/syllabus/serializers/teacher_workstation_serializer.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from syllabus.models.teacher_workstation import TeacherWorkStation


class TeacherMiniSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)


class TeacherWorkStationSerializer(serializers.ModelSerializer):
    # ✅ Teacher automatically from logged-in user
    teacher = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    # Read-only info for UI
    teacher_info = TeacherMiniSerializer(source="teacher", read_only=True)

    class Meta:
        model = TeacherWorkStation
        fields = [
            "id",
            "teacher",
            "teacher_info",
            "school_name",
            "district",
            "ward",
            "region",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "teacher_info", "created_at", "updated_at"]

    # -------------------------
    # Field validation
    # -------------------------
    def validate_school_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                _("Jina la shule halitakiwi kuwa fupi sana.")
            )
        return value.strip()

    # -------------------------
    # Object-level validation
    # -------------------------
    def validate(self, attrs):
        teacher = attrs["teacher"]

        # ❌ hairuhusiwi workstation zaidi ya moja kwa mwalimu
        qs = TeacherWorkStation.objects.filter(teacher=teacher)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                {"detail": _("Mwalimu huyu tayari ana workstation moja.")}
            )

        return attrs