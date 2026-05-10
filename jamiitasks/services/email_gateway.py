# jamiitasks/services/email_gateway.py

import os
import logging
import requests
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_EMAIL_PROVIDER = os.getenv("EMAIL_DEFAULT_PROVIDER", "smtp").lower()
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", 10))  # timeout kwa maombi ya HTTP

# ---------------------
# PROVIDERS
# ---------------------

def send_via_smtp(subject, message, recipient, html_message=None):
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            html_message=html_message,
            fail_silently=False
        )
        return {"status": "success", "provider": "smtp"}
    except Exception as e:
        raise Exception(f"SMTP Error: {str(e)}")


def send_via_sendgrid(subject, message, recipient, html_message=None):
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    if not SENDGRID_API_KEY:
        raise ValueError("Missing SendGrid API key.")

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "personalizations": [{
            "to": [{"email": recipient}],
            "subject": subject
        }],
        "from": {"email": settings.DEFAULT_FROM_EMAIL},
        "content": [{"type": "text/plain", "value": message}]
    }

    if html_message:
        data["content"].append({"type": "text/html", "value": html_message})

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=EMAIL_TIMEOUT)
    except requests.exceptions.RequestException as e:
        raise Exception(f"SendGrid Network Error: {str(e)}")

    if resp.status_code in [200, 202]:
        return {"status": "success", "provider": "sendgrid"}
    raise Exception(f"SendGrid Error: {resp.text}")


def send_via_mailgun(subject, message, recipient, html_message=None):
    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")

    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
        raise ValueError("Missing Mailgun credentials.")

    url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

    data = {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [recipient],
        "subject": subject,
        "text": message,
    }

    if html_message:
        data["html"] = html_message

    try:
        resp = requests.post(url, auth=("api", MAILGUN_API_KEY), data=data, timeout=EMAIL_TIMEOUT)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Mailgun Network Error: {str(e)}")

    if resp.status_code == 200:
        return {"status": "success", "provider": "mailgun"}
    raise Exception(f"Mailgun Error: {resp.text}")


# ---------------------
# PROVIDER MAP
# ---------------------

EMAIL_PROVIDERS = {
    "smtp": send_via_smtp,
    "sendgrid": send_via_sendgrid,
    "mailgun": send_via_mailgun,
}


# ---------------------
# MAIN FUNCTION
# ---------------------

def send_email(subject, message, recipient, html_message=None, provider=None, fallback=True):
    selected = provider or DEFAULT_EMAIL_PROVIDER
    tried = []

    providers_to_try = [selected] + [p for p in EMAIL_PROVIDERS if p != selected] if fallback else [selected]

    for name in providers_to_try:
        try:
            logger.info(f"Jaribio la kutuma email kwa {recipient} kupitia {name}")
            return EMAIL_PROVIDERS[name](subject, message, recipient, html_message)
        except Exception as e:
            logger.warning(f"{name} imeshindwa kutuma email: {e}")
            tried.append((name, str(e)))

    logger.error(f"Tatizo kwenye kutuma email kwa {recipient}. Providers tried: {tried}")
    return {"status": "failed", "tried": tried}