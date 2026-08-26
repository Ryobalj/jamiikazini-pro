# syllabus/views/question_views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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

    @action(detail=False, methods=["get"])
    def available_types(self, request):
        """Distinct question_type values actually in the bank for a
        subject_version - lets the Manual paper-builder only offer types
        that exist, instead of failing at generation time with a
        shortfall (e.g. a math subject only ever has calculation/
        short_answer, never mcq/matching/etc)."""
        subject_version = request.query_params.get("subject_version")
        if not subject_version:
            return Response([])
        # Question.Meta.ordering pulls extra columns into the SELECT, which
        # breaks .distinct() at the SQL level (every row differs once
        # created_at is included) - dedupe in Python instead.
        types = sorted(set(
            self.get_queryset().filter(is_active=True).values_list("question_type", flat=True)
        ))
        return Response(types)
