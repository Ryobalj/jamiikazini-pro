# kiini/permissions/wallet.py

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsTransactionOwnerOrInstitutionAdmin(BasePermission):
    """
    Ruhusu user kuona au kuandika transaction kama:
    - yeye ndiye mmiliki wa wallet
    - au ni INSTITUTION_ADMIN ya wallet husika
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.method in SAFE_METHODS:
            return obj.wallet.user == request.user or request.user.role == 'INSTITUTION_ADMIN'
        return obj.wallet.user == request.user
