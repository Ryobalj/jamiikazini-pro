# jamiitasks/services/sms_gateway.py

import os
import logging
import requests

logger = logging.getLogger(__name__)

# Environment config
DEFAULT_PROVIDER = os.getenv("SMS_DEFAULT_PROVIDER", "africastalking").lower()
SMS_SENDER_ID = os.getenv("SMS_SENDER_ID", "JAMII")

# --- PROVIDER FUNCTIONS ---

def send_with_africastalking(phone, message):
    """
    Tuma SMS kupitia Africa's Talking API.
    """
    api_username = os.getenv("SMS_API_USERNAME")
    api_key = os.getenv("SMS_API_KEY")
    url = "https://api.africastalking.com/version1/messaging"

    if not api_username or not api_key:
        raise ValueError("Missing Africa's Talking credentials.")

    headers = {
        "apiKey": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    payload = {
        "username": api_username,
        "to": phone,
        "message": message.encode("utf-8", errors="ignore"),
    }

    if SMS_SENDER_ID:
        payload["from"] = SMS_SENDER_ID

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=5)
        if response.status_code in [200, 201]:
            return {
                "status": "success",
                "provider": "africastalking",
                "response": response.json()
            }
        logger.error(f"[Africa'sTalking] HTTP {response.status_code}: {response.text}")
        raise Exception(f"HTTP Error {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"[Africa'sTalking] Network error: {str(e)}")
        raise


def send_with_twilio(phone, message):
    """
    Tuma SMS kupitia Twilio.
    """
    from twilio.rest import Client

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, from_number]):
        raise ValueError("Missing Twilio credentials.")

    try:
        client = Client(account_sid, auth_token)
        sent = client.messages.create(
            body=message,
            from_=from_number,
            to=phone
        )
        return {
            "status": "success",
            "provider": "twilio",
            "sid": sent.sid
        }
    except Exception as e:
        logger.error(f"[Twilio] Error sending SMS: {str(e)}")
        raise


def send_with_telerivet(phone, message):
    """
    Tuma SMS kupitia Telerivet API.
    """
    api_key = os.getenv("TELERIVET_API_KEY")
    project_id = os.getenv("TELERIVET_PROJECT_ID")
    phone_id = os.getenv("TELERIVET_PHONE_ID")

    if not all([api_key, project_id, phone_id]):
        raise ValueError("Missing Telerivet credentials.")

    url = f"https://api.telerivet.com/v1/projects/{project_id}/messages/send"
    payload = {
        "content": message,
        "phone_id": phone_id,
        "to_number": phone,
    }

    try:
        response = requests.post(url, auth=(api_key, ""), data=payload, timeout=5)
        if response.status_code in [200, 201]:
            return {
                "status": "success",
                "provider": "telerivet",
                "response": response.json()
            }
        logger.error(f"[Telerivet] HTTP {response.status_code}: {response.text}")
        raise Exception(f"HTTP Error {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"[Telerivet] Network error: {str(e)}")
        raise

# --- PROVIDER MAP ---

SMS_PROVIDERS = {
    "africastalking": send_with_africastalking,
    "twilio": send_with_twilio,
    "telerivet": send_with_telerivet,
}

# --- MAIN FUNCTION ---

def send_sms(phone, message, provider=None, fallback=True):
    """
    Tuma SMS ukitumia provider maalum au default.
    Ikiwa fallback=True, itajaribu provider wengine pia ikifeli.
    """
    selected = (provider or DEFAULT_PROVIDER).lower()
    providers_order = [selected] + [p for p in SMS_PROVIDERS if p != selected] if fallback else [selected]

    tried = []
    for name in providers_order:
        try:
            logger.info(f"[SMS] Jaribio la kutuma kwa {phone} kupitia {name}")
            return SMS_PROVIDERS[name](phone, message)
        except Exception as e:
            tried.append((name, str(e)))
            logger.warning(f"[SMS] Provider '{name}' imeshindwa: {e}")

    logger.error(f"[SMS] Kushindwa kutuma kwa {phone}. Majaribio: {tried}")
    return {"status": "failed", "tried": tried}