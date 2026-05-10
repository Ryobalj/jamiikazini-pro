# jamiikazini/syllabus/views/main_competence_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend

from syllabus.models.main_competence import MainCompetence
from syllabus.serializers.main_competence_serializer import MainCompetenceSerializer


class MainCompetenceViewSet(viewsets.ModelViewSet):
    """
    PRO-MAX ViewSet for MainCompetence
    - Auto ordering
    - Search + filtering + ordering
    - Faster queryset handling
    """

    serializer_class = MainCompetenceSerializer
    permission_classes = [IsAdminUser]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["subject_version"]
    search_fields = ["name"]
    ordering_fields = ["order", "created_at"]
    ordering = ["subject_version", "order"]

    def get_queryset(self):
        # Faster select_related for FK
        return MainCompetence.objects.select_related("subject_version").all()

    def perform_create(self, serializer):
        # AUTO-ORDERING per subject_version
        subject_version = serializer.validated_data["subject_version"]
        last_value = (
            MainCompetence.objects.filter(subject_version=subject_version)
            .aggregate(Max("order"))
            .get("order__max") or 0
        )
        serializer.save(order=last_value + 1)