# security/helpers/recaptcha.py

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def verify_recaptcha_v2(token, remote_ip=None):
    data = {
        "secret": settings.RECAPTCHA_PRIVATE_KEY,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=data, timeout=5)
        result = response.json()
        if not result.get("success"):
            logger.warning("reCAPTCHA v2 verification failed: %s", result.get("error-codes"))
        return result.get("success", False)
    except Exception:
        logger.exception("reCAPTCHA v2 siteverify request failed")
        return False


def verify_recaptcha_v3(token, remote_ip=None, expected_action=None):
    data = {
        "secret": settings.RECAPTCHA_PRIVATE_KEY_V3,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=data, timeout=5)
        result = response.json()

        if not result.get("success"):
            logger.warning("reCAPTCHA v3 verification failed: %s", result.get("error-codes"))
            return False
        if expected_action and result.get("action") != expected_action:
            logger.warning(
                "reCAPTCHA v3 action mismatch: expected=%s got=%s", expected_action, result.get("action")
            )
            return False
        if result.get("score", 0) < 0.5:
            logger.warning("reCAPTCHA v3 score too low: %s", result.get("score"))
            return False

        return True
    except Exception:
        logger.exception("reCAPTCHA v3 siteverify request failed")
        return False