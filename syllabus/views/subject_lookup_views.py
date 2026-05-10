from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from syllabus.models.subject import Subject
from syllabus.serializers.subject_lookup_serializer import SubjectLookupSerializer


class SubjectLookupView(ListAPIView):
    """
    Lightweight subject lookup for:
    - Timetable
    - Scheme of Work
    - Lesson Plan

    Optimized for dropdowns & autocomplete
    """
    serializer_class = SubjectLookupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Subject.objects.all().order_by("name")

        search = self.request.query_params.get("search")
        syllabus_year = self.request.query_params.get("syllabus_year")

        # 🔍 Search only when meaningful
        if search and len(search) >= 2:
            queryset = queryset.filter(name__icontains=search)

        # 📘 Filter by syllabus year if provided
        if syllabus_year:
            queryset = queryset.filter(
                syllabus_versions__year=syllabus_year
            )

        # ⚡ IMPORTANT: limit results for performance
        return queryset.distinct()[:20]