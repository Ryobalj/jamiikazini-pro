from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser
from syllabus.models.subject import Subject
from syllabus.serializers.subject_serializer import SubjectSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    """
    Subject management (ADMIN ONLY)

    - Full CRUD
    - Search by name & code
    - Ordering support
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminUser]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = ["name", "code"]
    ordering_fields = ["name", "code", "created_at"]
    ordering = ["name"]