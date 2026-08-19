# syllabus/serializers/generated_paper_serializers.py

from rest_framework import serializers

from syllabus.models.exam_format import ExamFormat, ExamFormatSection
from syllabus.models.question import Question
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.generated_paper import GeneratedPaper, GeneratedPaperQuestion
from syllabus.serializers.question_serializers import QuestionSerializer


class SectionTopicScopeSerializer(serializers.Serializer):
    """Automated mode: which topics apply to one of the CHOSEN
    exam_format's existing sections. A section absent here, or given an
    empty topic_ids, draws from every topic in the subject."""

    section = serializers.PrimaryKeyRelatedField(queryset=ExamFormatSection.objects.all())
    topic_ids = serializers.PrimaryKeyRelatedField(
        queryset=LearningActivity.objects.all(), many=True, required=False, default=list
    )


class CustomSlotSerializer(serializers.Serializer):
    """Manual mode: one 'N questions of type X, difficulty Y' rule within
    a teacher-built section."""

    question_type = serializers.ChoiceField(choices=Question.QuestionType.choices)
    difficulty = serializers.ChoiceField(choices=Question.Difficulty.choices, default=Question.Difficulty.MEDIUM)
    count = serializers.IntegerField(min_value=1)
    marks_per_item = serializers.IntegerField(min_value=1, default=1)


class CustomSectionSerializer(serializers.Serializer):
    """Manual mode: one teacher-defined section - its own name, question
    slots, and topic scope."""

    name = serializers.CharField(max_length=100)
    topic_ids = serializers.PrimaryKeyRelatedField(
        queryset=LearningActivity.objects.all(), many=True, required=False, default=list
    )
    slots = CustomSlotSerializer(many=True, allow_empty=False)


class GeneratePaperRequestSerializer(serializers.Serializer):
    """DTO for POSTing a new paper-generation request. Two mutually
    exclusive modes:
    - Automated ('otomatiki'): pass `exam_format` (+ optional
      `section_topics` to scope each of that format's existing sections
      to specific topics).
    - Manual ('mwenyewe'): pass `paper_type` + `custom_sections` - the
      teacher builds the whole paper's structure (sections, question-type/
      difficulty/count/marks slots, and per-section topics) from scratch.
    """

    # Automated mode
    exam_format = serializers.PrimaryKeyRelatedField(
        queryset=ExamFormat.objects.filter(is_active=True), required=False
    )
    section_topics = SectionTopicScopeSerializer(many=True, required=False, default=list)

    # Manual mode
    paper_type = serializers.ChoiceField(choices=ExamFormat.PaperType.choices, required=False)
    custom_sections = CustomSectionSerializer(many=True, required=False, default=list)
    time_allowed_minutes = serializers.IntegerField(required=False, allow_null=True)
    instructions = serializers.CharField(required=False, allow_blank=True, default="")

    subject_version = serializers.PrimaryKeyRelatedField(queryset=SubjectVersion.objects.all())
    title = serializers.CharField(required=False, allow_blank=True, default="")
    year = serializers.IntegerField(required=False, allow_null=True)
    term = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        has_format = bool(data.get("exam_format"))
        has_custom = bool(data.get("custom_sections"))
        if has_format and has_custom:
            raise serializers.ValidationError(
                "Toa ama exam_format (otomatiki) au custom_sections (mwenyewe), si vyote viwili."
            )
        if not has_format and not has_custom:
            raise serializers.ValidationError(
                "Toa ama exam_format (otomatiki) au custom_sections (mwenyewe)."
            )
        if has_custom and not data.get("paper_type"):
            raise serializers.ValidationError({"paper_type": "paper_type inahitajika kwa muundo wa mwenyewe."})
        if has_format:
            exam_format = data["exam_format"]
            valid_section_ids = set(exam_format.sections.values_list("id", flat=True))
            for scope in data.get("section_topics", []):
                if scope["section"].id not in valid_section_ids:
                    raise serializers.ValidationError({
                        "section_topics": f"Sehemu {scope['section'].id} siyo sehemu ya muundo huu wa mtihani."
                    })
        return data


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
