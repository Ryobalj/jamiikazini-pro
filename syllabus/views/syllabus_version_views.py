# syllabus/views/syllabus_version_views.py

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.serializers.syllabus_version_serializer import SyllabusVersionSerializer

class SyllabusVersionViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for SyllabusVersion
    - Admin only
    """
    queryset = SyllabusVersion.objects.all().order_by("-year")
    serializer_class = SyllabusVersionSerializer
    permission_classes = [IsAdminUser]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["year"]
    ordering_fields = ["year", "created_at"]
    ordering = ["-year"]