# security/middleware/conditional_2fa.py

import logging
from django.conf import settings
from django.http import JsonResponse
from security.utils.otp_helpers import parse_otp_token
from django.core.signing import BadSignature, SignatureExpired

logger = logging.getLogger(__name__)

# list of protected paths can be set in settings as regexes or exact strings
PROTECTED_PATHS = getattr(settings, "SECURITY_2FA_PROTECTED_PATHS", [
    r"^/api/v1/payments/.*$",
    r"^/api/v1/businesses/.*/settings/?$",
    r"^/api/v1/institutions/.*/sensitive-action/?$",
])

import re

class Conditional2FAMiddleware:
    """
    Middleware that blocks requests to protected endpoints unless OTP/TOTP has been
    verified recently.

    Accepts either:
      - a signed OTP token in header 'HTTP_X_OTP_TOKEN' (from otp_helpers.make_otp_token),
      - or session flag request.session['otp_verified'] with timestamp.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_patterns = [re.compile(p) for p in PROTECTED_PATHS]

    def _is_protected(self, path: str) -> bool:
        for pat in self.protected_patterns:
            if pat.search(path):
                return True
        return False

    def __call__(self, request):
        # Wakati wa tests (pytest) DRF force_authenticate haifiki middleware - ruka ukaguzi
        if getattr(settings, "TESTING", False):
            return self.get_response(request)

        path = request.path
        if self._is_protected(path):
            user = getattr(request, "user", None)
            # require authenticated user
            if not user or not getattr(user, "is_authenticated", False):
                return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)

            # 1) Check session-based verification (if using session)
            session = getattr(request, "session", None)
            if session:
                otp_verified = session.get("otp_verified", {})
                # otp_verified stored as dict: {"ts": <timestamp>, "scope": "..."}
                if isinstance(otp_verified, dict):
                    # expiry in settings
                    ttl = getattr(settings, "SECURITY_OTP_SESSION_TTL_SECONDS", 60 * 15)
                    ts = otp_verified.get("ts")
                    if ts and ( (int(ts) + int(ttl)) >= int(__import__("time").time()) ):
                        # ensure token belongs to user (optional: check user id)
                        if otp_verified.get("user_id") == user.id:
                            return self.get_response(request)

            # 2) Check header token
            header_token = request.META.get("HTTP_X_OTP_TOKEN")
            if header_token:
                try:
                    payload = parse_otp_token(header_token)
                    if int(payload.get("user_id")) == user.id:
                        return self.get_response(request)
                except SignatureExpired:
                    return JsonResponse({"detail": "OTP token expired."}, status=403)
                except BadSignature:
                    return JsonResponse({"detail": "Invalid OTP token."}, status=403)
                except Exception as e:
                    logger.exception("OTP header parse error")
                    return JsonResponse({"detail": "Invalid OTP token data."}, status=403)

            # Not verified -> block and instruct client to request OTP
            return JsonResponse({
                "detail": "2FA/OTP verification required for this action.",
                "2fa_required": True,
                "otp_request_url": getattr(settings, "SECURITY_OTP_REQUEST_URL", "/api/v1/security/otp/request/")
            }, status=403)

        # not protected
        return self.get_response(request)