# kiini/middleware/platform_lock.py

import re
from django.conf import settings
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from kiini.models.platform_lock import PlatformLock

# Njia zinazoruhusiwa hata mfumo ukiwa umefungwa: kuingia/kujiandikisha
# (bila hizi mtumiaji hawezi hata ku-login kuona kama amefunguliwa), JamiiShule
# (module pekee inayoachwa wazi), admin/static/docs za kawaida, na sehemu
# ndogo tu ya jamiiwallet inayohitajika kulipia usajili wa JamiiShule (angalia
# syllabus/services/subscription_service.py - malipo hutolewa moja kwa moja
# kwenye Wallet ya mwalimu; ikiwa salio halitoshi, mteja huelekezwa
# jamiiwallet kuweka pesa - njia hizo za kuweka pesa lazima ziendelee
# kufanya kazi, si Wallet nzima). Webhook ya PawaPay pia lazima ibaki wazi
# kabisa - inaitwa na seva za PawaPay zenyewe, si mtumiaji wa app.
EXEMPT_PATH_PATTERNS = getattr(settings, "PLATFORM_LOCK_EXEMPT_PATHS", [
    r"^/$",
    r"^/admin/",
    r"^/_nested_admin/",
    r"^/static/",
    r"^/media/",
    r"^/swagger",
    r"^/redoc",
    r"^/api/v1/security/token/",
    # The actual login/logout endpoints the frontend calls
    # (security/urls/auth_urls.py::UnifiedLoginView/LogoutView) - NOT the
    # same as /security/token/ above (that's the separate, currently-unused
    # simplejwt TokenObtainPairView). Missing this was the real bug: every
    # login attempt was getting 423'd while locked, so nobody - not even an
    # ADMIN trying to log in to unlock the platform - could sign in at all.
    r"^/api/v1/security/login/?$",
    r"^/api/v1/security/logout/?$",
    r"^/api/v1/auth/me/?$",
    r"^/api/v1/auth/register/?$",
    r"^/api/v1/auth/forgot-password/?$",
    r"^/api/v1/auth/reset-password",
    r"^/api/v1/auth/verify-email",
    r"^/api/v1/kiini/platform-status/?$",
    r"^/api/v1/kiini/user-menu/?$",
    r"^/api/v1/health/?$",
    r"^/api/v1/syllabus/",
    r"^/api/v1/jamiiwallet/wallet/?$",
    r"^/api/v1/jamiiwallet/topup/?$",
    r"^/api/v1/payments/webhooks/",
    r"^/api/v1/payments/exchange-rates/?$",
    r"^/api/v1/payments/currencies/?$",
])


class PlatformLockMiddleware:
    """
    Ikiwa PlatformLock.load().is_locked ni True, huzuia njia zote isipokuwa
    zilizo kwenye EXEMPT_PATH_PATTERNS (hasa /api/v1/syllabus/ - JamiiShule)
    kwa watumiaji wasio ADMIN. Lengo: kufungia jukwaa zima muda mfupi (mfano
    wakati wa kukamilisha uunganisho wa APIs za serikali) bila kuathiri
    JamiiShule wala uwezo wa admin kuendelea kufanya kazi/kufungua tena.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_patterns = [re.compile(p) for p in EXEMPT_PATH_PATTERNS]

    def _is_exempt(self, path: str) -> bool:
        return any(pat.search(path) for pat in self.exempt_patterns)

    def _resolve_user(self, request):
        # request.user (kutoka AuthenticationMiddleware) ni session-based
        # pekee - haitambui watumiaji wa JWT Bearer token (jinsi frontend
        # halisi inavyoauth), hivyo bila hii kila mtumiaji wa JWT (pamoja na
        # ADMIN halisi) angeonekana "hajaingia" na kufungiwa nje pia.
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            return user
        try:
            auth_result = JWTAuthentication().authenticate(request)
        except (InvalidToken, TokenError):
            return None
        if auth_result is None:
            return None
        jwt_user, _ = auth_result
        return jwt_user

    def __call__(self, request):
        if getattr(settings, "TESTING", False):
            return self.get_response(request)

        lock = PlatformLock.load()
        if not lock.is_locked:
            return self.get_response(request)

        if self._is_exempt(request.path):
            return self.get_response(request)

        user = self._resolve_user(request)
        if user and getattr(user, "is_authenticated", False) and getattr(user, "role", None) == "ADMIN":
            return self.get_response(request)

        return JsonResponse(
            {
                # Generic, technical - for API tooling/logs, not shown to users.
                "detail": "Platform is temporarily locked.",
                # User-facing text: blank unless the admin set a custom one.
                # The frontend falls back to its own translated
                # platform_lock.default_message when this is blank, instead
                # of always getting one hardcoded language regardless of the
                # visitor's chosen locale.
                "message": lock.message,
                "platform_locked": True,
            },
            status=423,
        )
