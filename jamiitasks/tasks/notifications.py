# jamiitasks/tasks/notifications.py

from celery import shared_task
from jamiitasks.services import sms_gateway, email_gateway, push_gateway
from jamiitasks.config.throttling import THROTTLE_LIMITS
import logging

logger = logging.getLogger(__name__)


# ================================
# ⚙️ Helper to fetch rate limits
# ================================
def get_rate_limit(task_name):
    """Return dynamic rate limit from THROTTLE_LIMITS."""
    return THROTTLE_LIMITS.get(f"jamiitasks.tasks.notifications.{task_name}", "30/m")


# ================================
# 📱 SMS Task
# ================================
@shared_task(
    bind=True,
    name="jamiitasks.tasks.notifications.send_sms_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=4,
    rate_limit=get_rate_limit("send_sms_task"),
)
def send_sms_task(self, phone, message):
    """
    Tuma SMS kupitia sms_gateway.
    Hutumia autoretry & dynamic throttling.
    """
    logger.info(f"[Task:{self.request.id}] Sending SMS to {phone}: {message}")

    try:
        result = sms_gateway.send_sms(phone, message)
        logger.info(f"[Task:{self.request.id}] SMS sent successfully to {phone}")
        return result
    except Exception as e:
        logger.error(f"[Task:{self.request.id}] SMS send error: {str(e)}")
        raise e


# ================================
# 📧 Email Task
# ================================
@shared_task(
    bind=True,
    name="jamiitasks.tasks.notifications.send_email_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    rate_limit=get_rate_limit("send_email_task"),
)
def send_email_task(self, to_email, subject, body):
    """
    Tuma barua pepe kupitia email_gateway.
    """
    logger.info(f"[Task:{self.request.id}] Sending email to {to_email} | Subject: {subject}")

    try:
        result = email_gateway.send_email(to_email, subject, body)
        logger.info(f"[Task:{self.request.id}] Email sent successfully to {to_email}")
        return result
    except Exception as e:
        logger.error(f"[Task:{self.request.id}] Email Task Error: {str(e)}")
        raise e


# ================================
# 🔔 Push Notification Task
# ================================
@shared_task(
    bind=True,
    name="jamiitasks.tasks.notifications.push_inapp_notification",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    rate_limit=get_rate_limit("push_inapp_notification"),
)
def send_push_notification_task(self, user_id, message):
    """
    Tuma notification ya ndani ya app (in-app / push).
    """
    logger.info(f"[Task:{self.request.id}] Sending push notification to user {user_id}: {message}")

    try:
        result = push_gateway.send_push(user_id, message)
        logger.info(f"[Task:{self.request.id}] Push notification sent to user {user_id}")
        return result
    except Exception as e:
        logger.error(f"[Task:{self.request.id}] Push Notification Error: {str(e)}")
        raise e