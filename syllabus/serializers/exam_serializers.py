# syllabus/serializers/exam_serializers.py

from decimal import Decimal
from rest_framework import serializers

from syllabus.models.student import Student
from syllabus.models.exam import Exam
from syllabus.models.mark import Mark
from syllabus.models.subject import Subject


class StudentSerializer(serializers.ModelSerializer):
    class_level_name = serializers.CharField(source="class_level.name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id", "workstation", "class_level", "class_level_name",
            "full_name", "gender", "admission_number", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")


class ExamSerializer(serializers.ModelSerializer):
    class_level_name = serializers.CharField(source="class_level.name", read_only=True)
    term_display = serializers.CharField(source="get_term_display", read_only=True)
    subject_names = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            "id", "workstation", "class_level", "class_level_name", "subjects",
            "subject_names", "name", "term", "term_display", "year",
            "max_score_per_subject", "created_at", "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def get_subject_names(self, obj):
        return [s.name for s in obj.subjects.all()]


class MarkSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Mark
        fields = ["id", "exam", "student", "student_name", "subject", "subject_name", "score"]
        read_only_fields = ("id",)


class BulkMarkEntrySerializer(serializers.Serializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    score = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0"))
