# jamiikazini/syllabus/views/specific_competence_views.py

import uuid

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from django.db.models import Max

from syllabus.models.specific_competence import SpecificCompetence
from syllabus.serializers.specific_competence_serializer import SpecificCompetenceSerializer


class SpecificCompetenceViewSet(viewsets.ModelViewSet):
    """
    PRO-MAX for SpecificCompetence
    - Nested filtering by main_competence
    - Auto ordering per main competence
    """

    serializer_class = SpecificCompetenceSerializer
    permission_classes = [IsAdminUser]

    filterset_fields = ["main_competence"]
    search_fields = ["name"]
    ordering_fields = ["order", "created_at"]
    ordering = ["main_competence", "order"]

    def get_queryset(self):
        queryset = (
            SpecificCompetence.objects
            .select_related("main_competence", "main_competence__subject_version")
            .all()
        )
        # Nested route: /main-competences/<pk>/specific-competences/
        main_competence_id = self.kwargs.get("main_competence_pk")
        if main_competence_id:
            try:
                uuid.UUID(str(main_competence_id))
            except (ValueError, TypeError):
                return queryset.none()
            queryset = queryset.filter(main_competence=main_competence_id)
        return queryset

    def perform_create(self, serializer):
        main_comp = serializer.validated_data["main_competence"]
        last_value = (
            SpecificCompetence.objects.filter(main_competence=main_comp)
            .aggregate(Max("order"))
            .get("order__max") or 0
        )
        serializer.save(order=last_value + 1)