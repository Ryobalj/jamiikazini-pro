# syllabus/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


class CanDownloadPDF(BasePermission):
    """
    Full document download (Azimio la Kazi, Andalio la Somo, Nukuu za
    Somo) requires an authenticated teacher with a currently-valid
    TeacherSubscription — the monthly fee is auto-debited from their
    JamiiWallet balance each renewal cycle (see subscription_service.py).
    Admins always have access.
    """

    message = "Huna usajili halali wa kupakua nyaraka hii. Tafadhali jaza salio la Wallet yako ili usajili wako uendelee."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if getattr(user, "role", None) == "ADMIN":
            return True

        from syllabus.services.subscription_service import has_full_access
        return has_full_access(user)


class IsAdminOrReadOnly(BasePermission):
    """Reference/lookup data (class levels, subjects) - any authenticated
    user can read it (needed so teachers can populate exam/timetable
    forms), but only Admins can create/edit/delete it."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(user, "role", None) == "ADMIN"


class IsAdminOrClientTeacher(BasePermission):
    """
    - ADMIN: full access
    - CLIENT (Teacher):
        * Can access only own Workstations & Timetables
        * Can CREATE workstation & timetable
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user

        # 🔐 Must be authenticated
        if not user or not user.is_authenticated:
            return False

        # 🛡 Admin can do everything
        if getattr(user, "role", None) == "ADMIN":
            return True

        # 👩‍🏫 Client teacher
        if getattr(user, "role", None) == "CLIENT":
            return True  # object-level will handle ownership

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user

        # 🛡 Admin bypass
        if getattr(user, "role", None) == "ADMIN":
            return True

        # 👩‍🏫 Client: object must belong to them
        # Support Workstation & Timetable
        owner = None

        if hasattr(obj, "teacher"):  # TeacherWorkStation
            owner = obj.teacher

        elif hasattr(obj, "workstation"):  # TimeTable
            owner = obj.workstation.teacher

        return owner == user