# kiini/views/staff_views.py

from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from kiini.models.staff import StaffProfile
from kiini.serializers.staff_serializers import StaffProfileSerializer
from kiini.permissions.access import IsInstitutionAdminOrReadOnly


class StaffProfileViewSet(viewsets.ModelViewSet):
    """
    CRUD view kwa StaffProfile chini ya taasisi maalum.
    Access inalindwa na institution check + role permissions.
    """
    serializer_class = StaffProfileSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdminOrReadOnly]

    def get_institution_pk(self):
        institution_pk = self.kwargs.get("institution_pk")
        if str(self.request.user.institution_id) != str(institution_pk):
            raise PermissionDenied("You do not have access to this institution.")
        return institution_pk

    def get_queryset(self):
        return StaffProfile.objects.filter(institution_id=self.get_institution_pk())

    def perform_create(self, serializer):
        serializer.save(institution_id=self.get_institution_pk())


class StaffProfileDetail(generics.RetrieveAPIView):
    """
    View ya kusoma StaffProfile mmoja, chini ya taasisi maalum.
    """
    serializer_class = StaffProfileSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdminOrReadOnly]

    def get_institution_pk(self):
        institution_pk = self.kwargs.get("institution_pk")
        if str(self.request.user.institution_id) != str(institution_pk):
            raise PermissionDenied("You do not have access to this institution.")
        return institution_pk

    def get_queryset(self):
        return StaffProfile.objects.filter(institution_id=self.get_institution_pk())