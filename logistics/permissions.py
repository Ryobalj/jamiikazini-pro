# logistics/permissions.py

from rest_framework import permissions


class IsTransporterOrAdmin(permissions.BasePermission):
    """
    Ruhusu tu watumiaji wenye role ya TRANSPORTER au ADMIN.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['TRANSPORTER', 'ADMIN']
        

class IsProviderOwnerOrReadOnly(permissions.BasePermission):
    """
    Ruhusu kusoma kwa wote lakini kuhariri ni kwa provider aliyehusika tu.
    """

    def has_object_permission(self, request, view, obj):
        # Ruhusu kusoma (GET, HEAD, OPTIONS) kwa wote waliologin
        if request.method in permissions.SAFE_METHODS:
            return True

        # Hapa, hakikisha user ana `transport_provider` na yeye ndiye mmiliki wa gari
        provider = request.user.transport_providers.first()
        obj_provider = getattr(obj, 'provider', None) or getattr(obj, 'transport_provider', None)
        return provider is not None and obj_provider == provider


class IsInstitutionOrBusiness(permissions.BasePermission):
    """
    Ruhusu tu watumiaji walio na role ya INSTITUTION_ADMIN au PROVIDER.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ['INSTITUTION_ADMIN', 'PROVIDER']
