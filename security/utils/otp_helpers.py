# security/utils/otp_helpers.py

import logging
from django.core import signing
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

OTP_SIGNING_SALT = getattr(settings, "SECURITY_OTP_SIGNING_SALT", "security-otp-salt")
OTP_SIGNING_MAX_AGE = getattr(settings, "SECURITY_OTP_TOKEN_MAX_AGE", 60 * 15)  # seconds (15m)
OTP_REQUEST_COOLDOWN = getattr(settings, "SECURITY_OTP_REQUEST_COOLDOWN", 30)   # seconds
OTP_REQUEST_LIMIT = getattr(settings, "SECURITY_OTP_REQUEST_LIMIT", 5)          # per window
OTP_REQUEST_WINDOW = getattr(settings, "SECURITY_OTP_REQUEST_WINDOW", 60 * 60)  # window seconds (1h)

def make_otp_token(user_id: int, scope: str = "general"):
    """
    Create a signed short-lived token that represents successful OTP verification
    (or that will be set after verify). This token can be passed in headers by clients.
    """
    payload = {"user_id": int(user_id), "scope": scope, "iat": timezone.now().timestamp()}
    token = signing.dumps(payload, salt=OTP_SIGNING_SALT)
    return token

def parse_otp_token(token: str, max_age: int = OTP_SIGNING_MAX_AGE):
    """
    Return payload or raise signing.SignatureExpired / signing.BadSignature
    """
    data = signing.loads(token, salt=OTP_SIGNING_SALT, max_age=max_age)
    return data

def mask_phone(phone: str) -> str:
    if not phone:
        return ""
    # keep last 3-4 digits
    digits = "".join([c for c in phone if c.isdigit()])
    if len(digits) <= 4:
        return f"***{digits}"
    return f"***{digits[-4:]}"

def mask_email(email: str) -> str:
    if not email:
        return ""
    try:
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            local_mask = "*" * len(local)
        else:
            local_mask = local[0] + ("*" * (len(local) - 2)) + local[-1]
        return f"{local_mask}@{domain}"
    except Exception:
        return "***@***"

# Simple rate-limit per identity (email or user_id) for OTP requests
def can_request_otp(identity: str) -> bool:
    """
    identity: e.g. f"user:{user_id}" or f"email:{email}"
    """
    key = f"security:otp:req:{identity}"
    data = cache.get(key)
    if not data:
        cache.set(key, 1, timeout=OTP_REQUEST_WINDOW)
        return True
    if data >= OTP_REQUEST_LIMIT:
        return False
    cache.incr(key)
    return True

def set_otp_cooldown(identity: str):
    key = f"security:otp:cool:{identity}"
    cache.set(key, True, timeout=OTP_REQUEST_COOLDOWN)

def is_in_cooldown(identity: str) -> bool:
    key = f"security:otp:cool:{identity}"
    return cache.get(key) is not None