from rest_framework import viewsets, filters
from syllabus.models.subject import Subject
from syllabus.serializers.subject_serializer import SubjectSerializer
from syllabus.permissions import IsAdminOrReadOnly


class SubjectViewSet(viewsets.ModelViewSet):
    """
    Subject management - read (list/retrieve) is open to any authenticated
    user (teachers need this to populate exam-results forms); write
    operations remain Admin-only.

    - Full CRUD
    - Search by name & code
    - Ordering support
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = ["name", "code"]
    ordering_fields = ["name", "code", "created_at"]
    ordering = ["name"]