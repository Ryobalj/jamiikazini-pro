# syllabus/views/subject_version_views.py

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser
from syllabus.models.subject_version import SubjectVersion
from syllabus.serializers.subject_version_serializer import SubjectVersionSerializer
from rest_framework.permissions import IsAuthenticated
from syllabus.serializers.subject_version_read_serializer import (
    SubjectVersionReadSerializer
)


class SubjectVersionViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for SubjectVersion
    - Admin only
    """
    queryset = SubjectVersion.objects.all().select_related(
        "syllabus_version", "subject", "class_level"
    )
    serializer_class = SubjectVersionSerializer
    permission_classes = [IsAdminUser]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["subject__name", "class_level__name"]
    ordering_fields = ["syllabus_version__year", "class_level__order", "order"]
    ordering = ["syllabus_version__year", "class_level__order", "order"]


class SubjectVersionReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    SubjectVersions read-only for authenticated teachers
    """
    queryset = SubjectVersion.objects.all().select_related(
        "syllabus_version", "subject", "class_level"
    )
    serializer_class = SubjectVersionReadSerializer
    permission_classes = [IsAuthenticated]
    pagenation_class = None

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["subject__name", "class_level__name"]
    ordering_fields = ["syllabus_version__year", "class_level__order", "order"]
    ordering = ["syllabus_version__year", "class_level__order", "order"]
