# gov_intergration/permissions/access.py

from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsVerificationOwnerOrInstitutionAdmin(BasePermission):
    """
    Ruhusu access kama user ndiye aliyeanzisha au ni institution admin.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user or request.user.role == 'INSTITUTION_ADMIN'
        return obj.user == request.user
