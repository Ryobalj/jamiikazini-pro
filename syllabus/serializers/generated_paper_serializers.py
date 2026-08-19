# syllabus/serializers/generated_paper_serializers.py

from rest_framework import serializers

from syllabus.models.exam_format import ExamFormat
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.generated_paper import GeneratedPaper, GeneratedPaperQuestion
from syllabus.serializers.question_serializers import QuestionSerializer


class GeneratePaperRequestSerializer(serializers.Serializer):
    """DTO for POSTing a new paper-generation request."""

    exam_format = serializers.PrimaryKeyRelatedField(queryset=ExamFormat.objects.filter(is_active=True))
    subject_version = serializers.PrimaryKeyRelatedField(queryset=SubjectVersion.objects.all())
    topic_ids = serializers.PrimaryKeyRelatedField(
        queryset=LearningActivity.objects.all(),
        many=True,
        required=False,
        default=list,
        help_text="Optional: restrict question selection to these topics only. Empty = all topics in the subject.",
    )
    title = serializers.CharField(required=False, allow_blank=True, default="")
    year = serializers.IntegerField(required=False, allow_null=True)
    term = serializers.IntegerField(required=False, allow_null=True)


class GeneratedPaperQuestionSerializer(serializers.ModelSerializer):
    question_detail = QuestionSerializer(source="question", read_only=True)

    class Meta:
        model = GeneratedPaperQuestion
        fields = ["id", "section_name", "order_in_section", "marks", "question", "question_detail"]
        read_only_fields = ("id",)


class GeneratedPaperSerializer(serializers.ModelSerializer):
    paper_questions = GeneratedPaperQuestionSerializer(many=True, read_only=True)
    exam_format_name = serializers.CharField(source="exam_format.name", read_only=True)
    subject_name = serializers.CharField(source="subject_version.subject.name", read_only=True)
    class_level_name = serializers.CharField(source="subject_version.class_level.name", read_only=True)

    class Meta:
        model = GeneratedPaper
        fields = [
            "id", "exam_format", "exam_format_name", "subject_version", "subject_name", "class_level_name",
            "workstation", "title", "year", "term", "created_at", "paper_questions",
        ]
        read_only_fields = ("id", "created_at", "workstation")
