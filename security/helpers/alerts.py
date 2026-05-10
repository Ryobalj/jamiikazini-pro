# security/helpers/alerts.py

import os
import requests
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_alert(message: str) -> None:
    """
    Send alert message to Slack using webhook.
    If webhook not configured, log locally.
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning(f"[Slack Alert Disabled] {message}")
        return

    try:
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=5
        )
        if resp.status_code != 200:
            logger.error(f"Slack alert failed: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"Slack alert exception: {e}")


def send_security_event(event: str, details: dict) -> None:
    """
    General security event notifier.
    Formats message + forwards to Slack + logs locally.
    """
    msg_lines = [f"🔐 Security Event: {event}"]
    for k, v in details.items():
        msg_lines.append(f"- {k}: {v}")
    message = "\n".join(msg_lines)

    logger.warning(message)
    send_slack_alert(message)


def alert_failed_otp(user, reason: str, ip: str, amount, currency: str) -> None:
    """
    Real-time alert for failed OTP attempts.
    """
    details = {
        "user": getattr(user, "id", None),
        "ip": ip,
        "amount": amount,
        "currency": currency,
        "reason": reason,
    }
    send_security_event("Failed OTP Attempt 🚨", details)


def alert_high_value_retries(user, ip: str, amount, currency: str, max_retries=3, window=300) -> None:
    """
    Alert if user retries high-value payment multiple times in a short period.
    Uses Django cache/Redis to track retry counts.
    """
    if not user:
        return

    key = f"high_value_retries:{user.id}"
    retries = cache.get(key, 0) + 1
    cache.set(key, retries, timeout=window)

    if retries >= max_retries:
        details = {
            "user": user.id,
            "ip": ip,
            "amount": amount,
            "currency": currency,
            "retries": retries,
            "window_sec": window,
        }
        send_security_event("Suspicious High-Value Payment Retries 🚨", details)