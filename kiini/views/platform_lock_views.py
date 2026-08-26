# kiini/views/platform_lock_views.py

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from kiini.models.platform_lock import PlatformLock

DEFAULT_LOCK_MESSAGE = (
    "Jamiikazini iko chini ya matengenezo ya muda mfupi tunapokamilisha "
    "uunganisho na mifumo ya serikali. JamiiShule inaendelea kupatikana kama "
    "kawaida."
)


class PlatformLockStatusView(APIView):
    """
    GET /kiini/platform-status/ - AllowAny, polled by the frontend on every
    load (logged in or not) to decide whether to show the platform-locked
    overlay. Never gated behind auth, otherwise a locked-out anonymous
    visitor could never even learn the platform is locked.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lock = PlatformLock.load()
        return Response({
            "is_locked": lock.is_locked,
            "message": lock.message or DEFAULT_LOCK_MESSAGE,
        })
