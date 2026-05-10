# jamiikazini/syllabus/serializers/subject_serializer.py

from rest_framework import serializers
from syllabus.models.subject import Subject


class SubjectSerializer(serializers.ModelSerializer):
    display = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            "id",
            "name",
            "code",
            "description",
            "periods_per_week",
            "created_at",
            "updated_at",
            "display",
        ]
        read_only_fields = ["code", "created_at", "updated_at"]

    def get_display(self, obj):
        return f"{obj.name} ({obj.code})"

    def validate_name(self, value):
        value = value.strip().title()
        qs = Subject.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Subject with this name already exists.")
        return value

    def validate_periods_per_week(self, value):
        if value < 1:
            raise serializers.ValidationError("Periods per week must be at least 1.")
        if value > 20:
            raise serializers.ValidationError("Periods per week seems too high.")
        return value
