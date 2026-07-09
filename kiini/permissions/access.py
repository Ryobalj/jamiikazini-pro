# kiini/permissions/access.py

from rest_framework import permissions
from rest_framework.permissions import BasePermission
from kiini.models.staff import StaffProfile


class IsInstitutionAdmin(BasePermission):
    """
    Ruhusu access kwa user mwenye role ya INSTITUTION_ADMIN.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'INSTITUTION_ADMIN'


class IsStaff(BasePermission):
    """
    Ruhusu access kwa user mwenye role ya STAFF.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'STAFF'


class IsClient(BasePermission):
    """
    Ruhusu access kwa CLIENT pekee (asiye na StaffProfile).
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'CLIENT'


class IsSuperAdmin(BasePermission):
    """
    Ruhusu access kwa is_superuser.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsStaffInInstitution(BasePermission):
    """
    Ruhusu access kama staff ni wa institution inayolingana.
    """
    def has_permission(self, request, view):
        if request.user.role != 'STAFF':
            return False
        try:
            staff = StaffProfile.objects.get(user=request.user)
            return staff.institution == getattr(request, 'institution', None)
        except StaffProfile.DoesNotExist:
            return False


class IsInstitutionUserOrReadOnly(BasePermission):
    """
    Ruhusu access ya andika kama user amehusishwa na institution, au read-only kwa wengine.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.institution is not None


class IsInstitutionAdminOrReadOnly(BasePermission):
    """
    Ruhusu access ya andika kama user ni INSTITUTION_ADMIN,
    lakini ruhusu POST kwa user yeyote aliye authenticated.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Writes: authenticated; umiliki hukaguliwa object-level
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if user.is_staff or user.is_superuser:
            return True
        # Mmiliki wa object (mf. Business.owner) anaruhusiwa kuhariri chake
        if getattr(obj, "owner_id", None) == user.id:
            return True
        return user.role == "INSTITUTION_ADMIN"


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


class IsBusinessOwnerOrReadOnly(BasePermission):
    """
    Ruhusu user mwenye role ya PROVIDER kuandika, wengine waone tu.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'PROVIDER'