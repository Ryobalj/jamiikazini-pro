# syllabus/serializers/exam_format_serializers.py

from rest_framework import serializers

from syllabus.models.exam_format import ExamFormat, ExamFormatSection, ExamFormatSlot


class ExamFormatSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamFormatSlot
        fields = ["id", "order", "question_type", "difficulty", "count", "marks_per_item"]
        read_only_fields = ("id",)


class ExamFormatSectionSerializer(serializers.ModelSerializer):
    slots = ExamFormatSlotSerializer(many=True, read_only=True)

    class Meta:
        model = ExamFormatSection
        fields = ["id", "order", "name", "slots"]
        read_only_fields = ("id",)


class ExamFormatSerializer(serializers.ModelSerializer):
    sections = ExamFormatSectionSerializer(many=True, read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True, default="")
    class_level_name = serializers.CharField(source="class_level.name", read_only=True, default="")

    class Meta:
        model = ExamFormat
        fields = [
            "id", "name", "paper_type", "subject", "subject_name", "class_level", "class_level_name",
            "time_allowed_minutes", "instructions", "total_marks", "is_active", "sections",
        ]
        read_only_fields = ("id", "total_marks")


class ExamFormatListSerializer(serializers.ModelSerializer):
    """Lightweight version for browsing/choosing a format - no nested sections."""
    subject_name = serializers.CharField(source="subject.name", read_only=True, default="")
    class_level_name = serializers.CharField(source="class_level.name", read_only=True, default="")

    class Meta:
        model = ExamFormat
        fields = [
            "id", "name", "paper_type", "subject", "subject_name", "class_level", "class_level_name",
            "time_allowed_minutes", "total_marks", "is_active",
        ]
