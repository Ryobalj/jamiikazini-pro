# security/decorators.py

from functools import wraps
from django.http import JsonResponse
from django.utils import timezone
from django.core.signing import BadSignature, SignatureExpired

from accounts.models import User
from security.utils.otp_helpers import parse_otp_token
from security.utils.auth_resolution import resolve_authenticated_user
import logging

logger = logging.getLogger(__name__)


def otp_required(scope="general", ttl_minutes=5):
    """
    Decorator for view functions that require OTP verification.
    - Accepts signed token in header 'X-OTP-Token'
    - Or session-based verification
    - ttl_minutes: validity of session-based verification
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(*args, **kwargs):
            from django.conf import settings
            if getattr(settings, "TESTING", False):
                # 2FA imezimwa kwenye mazingira ya vipimo
                return view_func(*args, **kwargs)
            # Find request
            if len(args) >= 2 and hasattr(args[1], 'user'):
                request = args[1]
            elif len(args) >= 1 and hasattr(args[0], 'user'):
                request = args[0]
            else:
                request = kwargs.get('request')
                
            if not request:
                return view_func(*args, **kwargs)

            user = resolve_authenticated_user(request)
            if not user or not user.is_authenticated:
                return JsonResponse({"detail": "Authentication required."}, status=401)

            # Check session
            session_otp = request.session.get("otp_verified", {})
            if (
                session_otp.get("user_id") == user.id
                and session_otp.get("scope") == scope
            ):
                verified_at = session_otp.get("verified_at")
                if verified_at:
                    age = (timezone.now() - timezone.datetime.fromisoformat(verified_at)).total_seconds()
                    if age <= ttl_minutes * 60:
                        return view_func(*args, **kwargs)
                    else:
                        logger.info(f"OTP session expired for user={user.id}, scope={scope}")

            # Token-based verification
            token = request.META.get("HTTP_X_OTP_TOKEN")
            if token:
                try:
                    payload = parse_otp_token(token)
                    if payload.get("scope") != scope:
                        logger.warning(f"OTP scope mismatch for user={user.id}")
                        return JsonResponse({"detail": "OTP scope mismatch."}, status=403)
                    if int(payload.get("user_id")) == user.id:
                        request.session["otp_verified"] = {
                            "user_id": user.id,
                            "scope": scope,
                            "verified_at": timezone.now().isoformat(),
                        }
                        return view_func(*args, **kwargs)
                except SignatureExpired:
                    logger.warning(f"Expired OTP token for user={user.id}")
                    return JsonResponse({"detail": "OTP token expired."}, status=403)
                except BadSignature:
                    logger.error(f"Invalid OTP token for user={user.id}")
                    return JsonResponse({"detail": "Invalid OTP token."}, status=403)

            return JsonResponse({"detail": "OTP verification required."}, status=403)

        return _wrapped
    return decorator


def conditional_2fa_required(action_type="general", ttl_minutes=5):
    """
    Enforce 2FA for specific critical actions.
    Works with both function-based and class-based views.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(*args, **kwargs):
            from django.conf import settings
            if getattr(settings, "TESTING", False):
                # 2FA imezimwa kwenye mazingira ya vipimo
                return view_func(*args, **kwargs)
            # Find request - handles both function and class-based views
            if len(args) >= 2 and hasattr(args[1], 'user'):
                request = args[1]  # self is args[0], request is args[1]
            elif len(args) >= 1 and hasattr(args[0], 'user'):
                request = args[0]
            else:
                request = kwargs.get('request')
                
            if not request:
                logger.warning("Could not find request, skipping 2FA check")
                return view_func(*args, **kwargs)

            user = resolve_authenticated_user(request)
            if not user or not user.is_authenticated:
                return JsonResponse({"detail": "Authentication required."}, status=401)

            # Kama 2FA haija-enabled, ruhusu
            if not user.is_2fa_enabled:
                return view_func(*args, **kwargs)

            action_types = [action_type] if isinstance(action_type, str) else action_type

            # Check session
            session_otp = request.session.get("otp_verified", {})
            if (
                session_otp.get("user_id") == user.id
                and session_otp.get("action_type") in action_types
            ):
                verified_at = session_otp.get("verified_at")
                if verified_at:
                    age = (timezone.now() - timezone.datetime.fromisoformat(verified_at)).total_seconds()
                    if age <= ttl_minutes * 60:
                        return view_func(*args, **kwargs)

            # Token-based check
            token = request.META.get("HTTP_X_OTP_TOKEN")
            if token:
                try:
                    payload = parse_otp_token(token)
                    if payload.get("scope") not in action_types:
                        logger.warning(f"OTP scope mismatch for user={user.id}")
                        return JsonResponse({"detail": "OTP scope mismatch."}, status=403)
                    if int(payload.get("user_id")) == user.id:
                        request.session["otp_verified"] = {
                            "user_id": user.id,
                            "action_type": payload.get("scope"),
                            "verified_at": timezone.now().isoformat(),
                        }
                        return view_func(*args, **kwargs)
                except SignatureExpired:
                    return JsonResponse({"detail": "OTP token expired."}, status=403)
                except BadSignature:
                    return JsonResponse({"detail": "Invalid OTP token."}, status=403)

            return JsonResponse({"detail": f"2FA required for {action_type}."}, status=403)

        return _wrapped
    return decorator