# jamiitasks/tasks/messaging.py

from celery import shared_task, current_app
import logging
from jamiitasks.services import messaging_gateway, notification_gateway
from jamiitasks.config.throttling import THROTTLE_LIMITS

logger = logging.getLogger(__name__)

# ================================
# ⚙️ Helper to fetch rate limits
# ================================
def get_rate_limit(task_name):
    """Return dynamic rate limit from THROTTLE_LIMITS."""
    return THROTTLE_LIMITS.get(f"jamiitasks.tasks.messaging.{task_name}", "60/m")


# ================================
# 💬 Chat Messaging Task
# ================================
@shared_task(
    bind=True,
    name="jamiitasks.tasks.messaging.send_chat_message",
    autoretry_for=(Exception,),
    retry_backoff=True,     # exponential delay e.g. 10s, 20s, 40s...
    retry_jitter=True,      # adds randomness to avoid thundering herd
    max_retries=5,          # allow up to 5 retries
    rate_limit=get_rate_limit("send_chat_message"),  # dynamic throttle
)
def send_chat_message(self, sender_id, recipient_id, message):
    """
    Kutuma ujumbe wa chat kutoka sender hadi recipient.
    Inatumia messaging_gateway na ina retries ikiwa kuna hitilafu.
    """
    logger.info(f"[Task:{self.request.id}] Kutuma ujumbe kutoka {sender_id} kwenda {recipient_id}...")

    if not message.strip():
        logger.warning(f"[Task:{self.request.id}] Ujumbe ni mweupe - skipping task.")
        return {"status": "failed", "reason": "Empty message"}

    try:
        response = messaging_gateway.send_chat_message(sender_id, recipient_id, message)
        logger.info(f"[Task:{self.request.id}] Chat message sent successfully.")
        return response
    except Exception as e:
        logger.error(f"[Task:{self.request.id}] Chat Message Task Error: {str(e)}")
        raise e  # autoretry_for itachukua control


# ================================
# 🔔 Notification Task
# ================================
@shared_task(
    bind=True,
    name="jamiitasks.tasks.messaging.notify_user_of_new_message",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    rate_limit=get_rate_limit("archive_old_conversations"),  # tunachukua limit ya messaging tasks
)
def notify_user_of_new_message(self, user_id):
    """
    Kumtaarifu mtumiaji kuwa ana ujumbe mpya kupitia push notification au njia nyingine.
    """
    logger.info(f"[Task:{self.request.id}] Kuandaa notification kwa user_id={user_id}...")

    try:
        response = notification_gateway.notify_new_message(user_id)
        logger.info(f"[Task:{self.request.id}] Notification sent successfully to user_id={user_id}.")
        return response
    except Exception as e:
        logger.error(f"[Task:{self.request.id}] Notification Task Error: {str(e)}")
        raise e