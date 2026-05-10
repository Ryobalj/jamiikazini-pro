# jamiitasks/tasks/security_tasks.py

import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction as db_transaction
from accounts.models import User, LoginHistory
from security.helpers.security import BaseLoginLogger


logger = logging.getLogger(__name__)


# =========================================
# ⚡ Suspicious Login / Failed Login Alerts
# =========================================
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def flag_suspicious_login(self, user_id: int, ip_address=None, user_agent=None, failed_type="login"):
    """
    Check failed login/OTP attempts and trigger alerts if threshold exceeded.
    This task is throttled via Celery rate limits.
    """
    try:
        from security.helpers.login_alerts import check_failed_logins_and_alert  # 👈 moved here

        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning(f"[Security] User with id={user_id} not found.")
        return "USER_NOT_FOUND"

    try:
        alerted = check_failed_logins_and_alert(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            failed_type=failed_type
        )
        if alerted:
            logger.info(f"[Security] Alert triggered for user {user.email} ({failed_type}).")
        else:
            logger.debug(f"[Security] No alert needed for user {user.email} ({failed_type}).")
        return alerted
    except Exception as e:
        logger.error(f"[Security] Error processing suspicious login for user {user.email}: {e}", exc_info=True)
        self.retry(exc=e, countdown=30)


# =========================================
# 🗄️ Audit / Login History Maintenance
# =========================================
@shared_task(bind=True)
def run_audit_log_rotation(self):
    """
    Archive or delete old login history logs.
    Can be scheduled daily/weekly.
    """
    try:
        retention_days = 90
        cutoff_date = timezone.now() - timezone.timedelta(days=retention_days)

        old_logs = LoginHistory.objects.filter(login_time__lt=cutoff_date)
        count = old_logs.count()
        old_logs.delete()

        logger.info(f"[Security] Audit log rotation completed. Deleted {count} old login entries.")
        return count
    except Exception as e:
        logger.error(f"[Security] Error during audit log rotation: {e}", exc_info=True)
        raise e


# =========================================
# 📢 Notify Admin of Security Events
# =========================================
@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def notify_admin_security_event(self, event_type: str, details: str):
    """
    Notify internal admin of critical security events (failed login spikes, suspicious activity, etc.)
    Can use email/SMS/Slack integration.
    """
    try:
        from security.helpers.alerts import send_slack_alert

        message = f"[SECURITY EVENT] Type: {event_type}\nDetails: {details}"
        send_slack_alert(message)

        logger.info(f"[Security] Admin notified of event '{event_type}'.")
        return "NOTIFIED"
    except Exception as e:
        logger.error(f"[Security] Failed to notify admin for event '{event_type}': {e}", exc_info=True)
        self.retry(exc=e, countdown=60)


# =========================================
# 🔄 Clean up expired OTP requests
# =========================================
@shared_task(bind=True)
def cleanup_expired_otps(self):
    """
    Delete expired OTP requests from LoginHistory.
    """
    try:
        from security.models import OTPRequest  # assuming this model exists
        ttl_seconds = 60 * 15  # 15 min
        cutoff_time = timezone.now() - timezone.timedelta(seconds=ttl_seconds)
        expired = OTPRequest.objects.filter(created_at__lt=cutoff_time)
        count = expired.count()
        expired.delete()
        logger.info(f"[Security] Cleaned up {count} expired OTP requests.")
        return count
    except Exception as e:
        logger.error(f"[Security] Error cleaning expired OTPs: {e}", exc_info=True)
        raise e