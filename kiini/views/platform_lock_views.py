# kiini/views/platform_lock_views.py

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from kiini.models.platform_lock import PlatformLock


class PlatformLockStatusView(APIView):
    """
    GET /kiini/platform-status/ - AllowAny, polled by the frontend on every
    load (logged in or not) to decide whether to show the platform-locked
    overlay. Never gated behind auth, otherwise a locked-out anonymous
    visitor could never even learn the platform is locked.

    `message` is returned as-is (blank unless the admin set a custom one) -
    deliberately NOT defaulted to a hardcoded string here. The frontend
    renders its own translated platform_lock.default_message when this is
    blank, so every user sees the notice in their own language instead of
    always getting one hardcoded language regardless of locale.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lock = PlatformLock.load()
        return Response({
            "is_locked": lock.is_locked,
            "message": lock.message,
        })
