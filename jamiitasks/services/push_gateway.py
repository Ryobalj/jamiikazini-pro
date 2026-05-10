# jamiitasks/services/push_gateway.py

import logging
import requests
import os

logger = logging.getLogger(__name__)

FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")
FCM_URL = "https://fcm.googleapis.com/fcm/send"


def _fcm_post(payload, headers):
    """
    Separated FCM POST request for easier testing/mocking.
    """
    return requests.post(FCM_URL, json=payload, headers=headers, timeout=5)


def send_push(user_id, message, device_token=None, title="Jamiikazini", data=None, retry=False, server_key=None):
    """
    Tuma push notification kupitia Firebase Cloud Messaging (FCM).

    :param user_id: ID ya mtumiaji
    :param message: Ujumbe wa notification
    :param device_token: Token ya kifaa
    :param title: Kichwa cha notification
    :param data: Data ya ziada
    :param retry: Ijaribu tena ikifeli
    :param server_key: (optional) FCM key mbadala, useful kwa testing
    :return: dict yenye status na response
    """
    server_key = server_key or FCM_SERVER_KEY

    if not server_key:
        logger.critical("FCM_SERVER_KEY haijapatikana kwenye mazingira.")
        raise ValueError("FCM server key is missing.")

    if not device_token:
        logger.warning(f"[FCM] Hakuna device_token kwa user_id={user_id}")
        return {"status": "skipped", "reason": "no device_token"}

    payload = {
        "to": device_token,
        "notification": {
            "title": title,
            "body": message,
            "sound": "default",
            "click_action": "FLUTTER_NOTIFICATION_CLICK"
        },
        "data": data or {},
        "priority": "high"
    }

    headers = {
        "Authorization": f"key={server_key}",
        "Content-Type": "application/json"
    }

    try:
        response = _fcm_post(payload, headers)

        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("success") == 1:
                logger.info(f"[FCM] Push imetumwa kwa user_id={user_id}")
                return {"status": "success", "response": res_json}
            else:
                logger.warning(f"[FCM] Push partial failure kwa user_id={user_id}: {res_json}")
                return {
                    "status": "partial_failure",
                    "response": res_json,
                    "error": res_json.get("results", [{}])[0].get("error", "Unknown error")
                }

        logger.error(f"[FCM] Hitilafu ya HTTP {response.status_code}: {response.text}")
        return {"status": "failed", "http_status": response.status_code, "error": response.text}

    except requests.exceptions.RequestException as e:
        logger.error(f"[FCM] Network error: {str(e)}")

        if retry:
            logger.info("[FCM] Inaonekana kuna tatizo la mtandao, tunajaribu tena (retry=False)...")
            return send_push(user_id, message, device_token, title, data, retry=False, server_key=server_key)

        return {"status": "network_error", "error": str(e)}