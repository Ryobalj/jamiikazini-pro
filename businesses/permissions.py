import logging
from rest_framework import permissions

logger = logging.getLogger(__name__)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Ruhusu user mwenye review ku-edit au kufuta, wengine waone tu.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
      

class IsBookingOwnerOrStaffOrReadOnly(permissions.BasePermission):
    """
    Ruhusu tu:
    - Mmiliki wa booking (client)
    - Staff user
    - Kusoma tu (GET, HEAD, OPTIONS) kwa watu wengine
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        is_owner = obj.client == user
        is_staff = user.is_staff or getattr(user, "role", "") == "INSTITUTION_ADMIN"

        # Ruhusu kusoma tu kwa wengine
        if request.method in permissions.SAFE_METHODS:
            return is_owner or is_staff

        # Ruhusu kuandika tu kwa owner au staff
        return is_owner or is_staff