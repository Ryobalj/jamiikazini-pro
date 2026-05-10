# security/helpers/payment_otp.py

import logging
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired
from django.core.cache import cache

from security.utils.otp_helpers import parse_otp_token
from payments.services.currency_service import convert_to_default
from security.helpers.alerts import alert_failed_otp, alert_high_value_retries
from payments.models.audit_log import AuditLog, AuditAction

logger = logging.getLogger(__name__)

# Configurable settings
RETRY_THRESHOLD = getattr(settings, "SECURITY_HIGH_VALUE_PAYMENT_RETRY_THRESHOLD", 3)
CACHE_TTL = getattr(settings, "SECURITY_HIGH_VALUE_PAYMENT_RETRY_CACHE_TTL", 3600)  # seconds
HIGH_VALUE_THRESHOLD = getattr(settings, "SECURITY_HIGH_VALUE_PAYMENT_THRESHOLD", 10_000)
BASE_CURRENCY = getattr(settings, "DEFAULT_CURRENCY", "TZS")


def get_client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def enforce_high_value_otp(request, user, amount, currency=None):
    """
    Enforce OTP verification for high-value payments.
    Tracks failed attempts, triggers alerts, and logs audit entries.
    """
    if not currency:
        currency = BASE_CURRENCY

    # Convert amount to base currency
    try:
        amount_in_base = convert_to_default(Decimal(str(amount)), currency)
    except Exception as e:
        logger.warning(
            f"[HighValueOTP] Conversion failed user={user.id} amount={amount} currency={currency}: {e}"
        )
        amount_in_base = Decimal("0")

    if amount_in_base < Decimal(str(HIGH_VALUE_THRESHOLD)):
        logger.debug(f"[HighValueOTP] Payment below threshold: {amount_in_base} {BASE_CURRENCY}")
        return  # No OTP required

    ip = get_client_ip(request)
    retry_key = f"high_value_otp_retry:{user.id}:{ip}"
    retry_count = cache.get(retry_key, 0)

    token = request.META.get("HTTP_X_OTP_TOKEN")
    if not token:
        _handle_failed_otp(user, request, ip, amount, currency, retry_count, reason="missing_token")
        raise PermissionDenied("OTP verification required for high-value payment")

    try:
        payload = parse_otp_token(token)

        # Validate user_id
        if int(payload.get("user_id")) != user.id:
            _handle_failed_otp(user, request, ip, amount, currency, retry_count, reason="user_mismatch")
            raise PermissionDenied("OTP token invalid for this user")

        # Validate scope
        if payload.get("scope") not in ("high_value_payment", "general"):
            _handle_failed_otp(user, request, ip, amount, currency, retry_count, reason="scope_mismatch")
            raise PermissionDenied("OTP scope mismatch for high-value payment")

    except SignatureExpired:
        _handle_failed_otp(user, request, ip, amount, currency, retry_count, reason="expired")
        raise PermissionDenied("OTP token expired")

    except BadSignature:
        _handle_failed_otp(user, request, ip, amount, currency, retry_count, reason="invalid_signature")
        raise PermissionDenied("Invalid OTP token")

    # OTP success → reset retry counter
    cache.delete(retry_key)

    # Audit log for success
    AuditLog.log_from_request(
        request,
        user,
        action=AuditAction.SUCCESSFUL_2FA,
        description=f"Successful OTP for high-value payment {amount} {currency}",
        metadata={"amount": str(amount), "currency": currency, "ip": ip},
    )

    logger.info(f"[HighValueOTP] OTP verified successfully for user={user.id} amount={amount} {currency}")


def _handle_failed_otp(user, request, ip, amount, currency, retry_count, reason: str):
    """
    Centralized handler for failed OTP attempts:
    - Logs audit
    - Increments retry counter
    - Sends alerts if threshold exceeded
    """
    retry_count += 1
    cache.set(f"high_value_otp_retry:{user.id}:{ip}", retry_count, CACHE_TTL)

    # Audit log
    AuditLog.log_from_request(
        request,
        user,
        action=AuditAction.FAILED_2FA,
        description=f"Failed OTP for high-value payment {amount} {currency}",
        metadata={
            "amount": str(amount),
            "currency": currency,
            "ip": ip,
            "reason": reason,
            "retry_count": retry_count,
        },
    )

    # Alerts
    alert_failed_otp(user, reason=reason, ip=ip, amount=amount, currency=currency)
    if retry_count >= RETRY_THRESHOLD:
        alert_high_value_retries(user, ip=ip, amount=amount, currency=currency, retry_count=retry_count)