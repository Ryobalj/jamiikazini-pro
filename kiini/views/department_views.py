# kiini/views/department_views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from kiini.models.department import Department
from kiini.serializers.department_serializers import DepartmentSerializer
from kiini.permissions.access import IsInstitutionAdminOrReadOnly


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    Manages departments within a specific institution (via nested routing),
    ensuring only users belonging to the institution can access.
    """
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdminOrReadOnly]

    def get_institution_pk(self):
        institution_pk = self.kwargs.get("institution_pk")
        if str(self.request.user.institution_id) != str(institution_pk):
            raise PermissionDenied("You do not have access to this institution.")
        return institution_pk

    def get_queryset(self):
        return Department.objects.filter(institution_id=self.get_institution_pk())

    def perform_create(self, serializer):
        serializer.save(institution_id=self.get_institution_pk())