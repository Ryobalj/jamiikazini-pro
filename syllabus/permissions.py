# syllabus/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


class CanDownloadPDF(BasePermission):
    """
    Temporary simple permission.
    Later this will be replaced with subscription logic.
    """

    message = "You are not allowed to download this document."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
        )


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