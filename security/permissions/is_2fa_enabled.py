# security/permissions/is_2fa_enabled.py

from rest_framework.permissions import BasePermission

class Is2FAEnabled(BasePermission):
    """
    Allows access only if the user has enabled 2FA.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_2fa_enabled