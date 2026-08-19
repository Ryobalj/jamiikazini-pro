# syllabus/views/question_views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from syllabus.models.question import Passage, Question
from syllabus.serializers.question_serializers import PassageSerializer, QuestionSerializer


class PassageViewSet(viewsets.ModelViewSet):
    serializer_class = PassageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Passage.objects.select_related("learning_activity").all()
        learning_activity = self.request.query_params.get("learning_activity")
        if learning_activity:
            qs = qs.filter(learning_activity=learning_activity)
        return qs


class QuestionViewSet(viewsets.ModelViewSet):
    """CRUD for the question bank. Same access pattern as
    SpecificLearningActivityViewSet - the bank is teacher-facing curriculum
    content, not student-facing, so IsAuthenticated is the established
    precedent for this kind of data in this app."""

    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["learning_activity", "question_type", "difficulty", "is_active", "language"]

    def get_queryset(self):
        qs = Question.objects.select_related("learning_activity", "passage").all()
        subject_version = self.request.query_params.get("subject_version")
        if subject_version:
            qs = qs.filter(
                learning_activity__specific_competence__main_competence__subject_version=subject_version
            )
        return qs
