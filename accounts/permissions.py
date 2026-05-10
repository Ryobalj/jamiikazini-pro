# accounts/permissions.py

from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """Allows access only to admin users."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'

class IsInstitutionAdmin(BasePermission):
    """Allows access only to institution admin users."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'INSTITUTION_ADMIN'

class IsProvider(BasePermission):
    """Allows access only to service providers."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'PROVIDER'

class IsTransporter(BasePermission):
    """Allows access only to transport providers."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'TRANSPORTER'

class IsClient(BasePermission):
    """Allows access only to regular clients."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'CLIENT'

class IsOwnerOrAdmin(BasePermission):
    """
    Allows access to object owners or admins.

    Use this when the object has a `user` foreign key.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (obj.user == request.user or request.user.role == 'ADMIN')

class IsSameUserOrAdmin(BasePermission):
    """
    Allows users to edit their own profile or admins.

    Use this when the object *is* the user.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (obj == request.user or request.user.role == 'ADMIN')
