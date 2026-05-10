# security/helpers/recaptcha.py

import requests
from django.conf import settings


def verify_recaptcha_v2(token, remote_ip=None):
    data = {
        "secret": settings.RECAPTCHA_PRIVATE_KEY,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=data)
        result = response.json()
        return result.get("success", False)
    except Exception:
        return False


def verify_recaptcha_v3(token, remote_ip=None, expected_action=None):
    data = {
        "secret": settings.RECAPTCHA_PRIVATE_KEY_V3,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=data)
        result = response.json()

        if not result.get("success"):
            return False
        if expected_action and result.get("action") != expected_action:
            return False
        if result.get("score", 0) < 0.5:
            return False

        return True
    except Exception:
        return False