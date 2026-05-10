# businesses/views/branch_views.py

from rest_framework import viewsets, permissions
from businesses.models.branch import Branch
from businesses.serializers.branch_serializer import BranchSerializer
from kiini.permissions.access import IsInstitutionAdminOrReadOnly
from security.decorators import conditional_2fa_required


class BranchViewSet(viewsets.ModelViewSet):
    """
    BranchViewSet:
    - CRUD ya matawi ya biashara
    - Admin actions zinahitaji 2FA
    """
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstitutionAdminOrReadOnly]

    def get_queryset(self):
        return Branch.objects.filter(business_id=self.kwargs['business_pk'])

    @conditional_2fa_required(action_type="admin_action")
    def perform_create(self, serializer):
        serializer.save(business_id=self.kwargs['business_pk'])

    @conditional_2fa_required(action_type="admin_action")
    def perform_update(self, serializer):
        serializer.save()

    @conditional_2fa_required(action_type="admin_action")
    def perform_destroy(self, instance):
        instance.delete()