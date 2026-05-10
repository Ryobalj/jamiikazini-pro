# syllabus/views/learning_activity_views.py
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend

from syllabus.models.learning_activity import LearningActivity
from syllabus.serializers.learning_activity_serializer import LearningActivitySerializer


class LearningActivityViewSet(viewsets.ModelViewSet):
    serializer_class = LearningActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Support BOTH nested and direct filtering
        """
        # Check for nested parameter (from URL)
        specific_competence_id = self.kwargs.get('specific_competence_pk')
        
        # Check for direct parameter (from query string)
        subject_version_id = self.request.query_params.get('subject_version')
        
        queryset = LearningActivity.objects.select_related(
            "specific_competence",
            "specific_competence__main_competence",
            "specific_competence__main_competence__subject_version",
        ).all()

        # Priority: Nested parameter first
        if specific_competence_id:
            queryset = queryset.filter(specific_competence=specific_competence_id)
        # Then direct parameter
        elif subject_version_id:
            queryset = queryset.filter(
                specific_competence__main_competence__subject_version=subject_version_id
            )
        
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Handle both nested and direct requests
        """
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"error": str(e), "detail": "Failed to load learning activities"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )