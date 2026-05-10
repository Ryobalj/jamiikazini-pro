# security/permissions/require_2fa.py

from rest_framework.permissions import BasePermission

class Require2FA(BasePermission):
    """
    Ruhusu tu watumiaji waliowasha 2FA.
    """
    def has_permission(self, request, view):
        user = request.user

        # Kama hajalogin, apigwe denial
        if not user or not user.is_authenticated:
            return False

        # Ruhusu tu ikiwa 2FA imewashwa
        return user.is_2fa_enabled