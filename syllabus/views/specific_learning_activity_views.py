# syllabus/views/specific_learning_activity_views.py
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend

from syllabus.models.specific_learning_activity import SpecificLearningActivity
from syllabus.serializers.specific_learning_activity_serializer import SpecificLearningActivitySerializer


class SpecificLearningActivityViewSet(viewsets.ModelViewSet):
    serializer_class = SpecificLearningActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Support BOTH nested and direct filtering
        """
        # Check for nested parameter (from URL)
        learning_activity_id = self.kwargs.get('learning_activity_pk')
        
        # Check for direct parameter (from query string)
        learning_activity_qs = self.request.query_params.get('learning_activity')
        
        queryset = SpecificLearningActivity.objects.select_related(
            "learning_activity",
            "learning_activity__specific_competence",
        ).all()

        # Priority: Nested parameter first
        if learning_activity_id:
            queryset = queryset.filter(learning_activity=learning_activity_id)
        # Then direct parameter
        elif learning_activity_qs:
            queryset = queryset.filter(learning_activity=learning_activity_qs)
        
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Handle both nested and direct requests
        """
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"error": str(e), "detail": "Failed to load specific learning activities"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )