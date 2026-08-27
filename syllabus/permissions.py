# syllabus/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


class CanDownloadPDF(BasePermission):
    """
    Full document download (Azimio la Kazi, Andalio la Somo, Nukuu za
    Somo, ratiba, matokeo, karatasi za mtihani) requires an authenticated
    teacher who either has a currently-valid TeacherSubscription (the
    monthly fee is auto-debited from their JamiiWallet balance each
    renewal cycle - see subscription_service.py) or still has free-trial
    downloads left (subscription_service.FREE_DOWNLOAD_LIMIT). Admins
    always have access.

    Read-only: this only decides eligibility, it never spends a free
    download - some views call has_permission() more than once per
    request (e.g. once to gate the actual PDF, again for an unrelated
    JSON preview/metadata flag), so mutating state here would risk
    burning a free credit on a request that never even downloaded
    anything. See subscription_service.consume_free_download() for the
    actual spend, which views call explicitly once a document is really
    about to be handed back.
    """

    message = "Huna usajili halali wa kupakua nyaraka hii. Tafadhali jaza salio la Wallet yako ili usajili wako uendelee."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if getattr(user, "role", None) == "ADMIN":
            return True

        from syllabus.services.subscription_service import has_full_access, has_free_downloads_remaining
        return has_full_access(user) or has_free_downloads_remaining(user)


class FreeDownloadGateMixin:
    """
    Mix into any APIView whose ENTIRE job is producing one downloadable
    document (PDF/XLSX) - i.e. it's already gated by
    `permission_classes = [IsAuthenticated, CanDownloadPDF]` and does
    nothing else. Spends one free-trial download (no-op for admins/paid
    subscribers) exactly once, right after the response has actually
    succeeded.

    Do NOT mix this into a dual-purpose view that also serves a plain
    JSON preview/metadata response from the same handler (e.g.
    SchemeCreateAPIView, AutoLessonPlanCreateAPIView) - every successful
    response through this mixin consumes a credit, which would wrongly
    charge a preview-only request. Those views call
    subscription_service.consume_free_download() explicitly, only inside
    their actual `?format=pdf` branch.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False) and 200 <= response.status_code < 300:
            from syllabus.services.subscription_service import consume_free_download
            consume_free_download(user)
        return response


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