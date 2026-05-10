# syllabus/views/timetable_views.py

from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from syllabus.models.timetable import TimeTable
from syllabus.serializers.timetable_serializer import TimeTableSerializer
from syllabus.models.teacher_workstation import TeacherWorkStation

class TimeTableViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for TimeTable
    """
    serializer_class = TimeTableSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "workstation__teacher__full_name",
        "subject_version__subject__name",
        "subject_version__class_level__name"
    ]
    ordering_fields = ["period", "timestart", "timefinish"]
    ordering = ["period"]

    def get_queryset(self):
        user = self.request.user
        qs = TimeTable.objects.all().select_related(
            "workstation", 
            "subject_version", 
            "subject_version__subject",
            "subject_version__class_level",
            "subject_version__syllabus_version"
        ).prefetch_related(
            # Add any prefetch relationships if needed
        )
        if user.role == "CLIENT":
            qs = qs.filter(workstation__teacher=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        # Hakikisha mwalimu anatumia workstation yake tu
        if user.role == "CLIENT":
            ws = serializer.validated_data.get('workstation')
            if ws and ws.teacher != user:
                return Response(
                    {"detail": "Unaweza tu kutumia workstation yako mwenyewe."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        serializer.save()
