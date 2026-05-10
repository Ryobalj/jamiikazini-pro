# syllabus/views/teacher_workstation_views.py

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.serializers.teacher_workstation_serializer import TeacherWorkStationSerializer


class TeacherWorkStationViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for TeacherWorkStation
    - Admin can manage all workstations
    - Client can manage only their own workstation
    """
    serializer_class = TeacherWorkStationSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["teacher__full_name", "school_name", "district", "region"]
    ordering_fields = ["school_name", "district", "ward", "region"]
    ordering = ["school_name", "district"]

    def get_queryset(self):
        user = self.request.user
        qs = TeacherWorkStation.objects.all().select_related("teacher")
        if user.role == "CLIENT":
            qs = qs.filter(teacher=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == "CLIENT":
            serializer.save(teacher=user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == "CLIENT" and serializer.instance.teacher != user:
            raise PermissionDenied("Not allowed to update this workstation")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role == "CLIENT" and instance.teacher != user:
            raise PermissionDenied("Not allowed to delete this workstation")
        instance.delete()