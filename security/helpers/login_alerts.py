# security/helpers/login_alerts.py

from django.utils import timezone
from accounts.models import LoginHistory, User
from jamiitasks.tasks.notifications import send_sms_task, send_email_task
from django.conf import settings

FAILED_LOGIN_THRESHOLD = 5        # max failed logins allowed
FAILED_OTP_THRESHOLD = 5          # max failed OTP attempts allowed
WINDOW_MINUTES = 15                # rolling window
ALERT_THROTTLE_MINUTES = 30        # don't resend alert within X minutes

def check_failed_logins_and_alert(user: User, ip_address=None, user_agent=None, failed_type="login"):
    """
    Scan recent failed logins or OTP attempts for a user and trigger alert if threshold exceeded.
    failed_type: "login" or "otp"
    """
    now = timezone.now()
    window_start = now - timezone.timedelta(minutes=WINDOW_MINUTES)

    if failed_type == "login":
        failed_attempts_qs = LoginHistory.objects.filter(
            user=user,
            was_successful=False,
            login_time__gte=window_start
        )
        alert_prefix = "failed login"
    elif failed_type == "otp":
        failed_attempts_qs = LoginHistory.objects.filter(
            user=user,
            was_successful=False,
            login_time__gte=window_start,
            otp_attempt=True  # assume LoginHistory tracks OTP attempts
        )
        alert_prefix = "failed OTP"
    else:
        return False

    # Optional: filter by IP/device for suspicious detection
    if ip_address:
        failed_attempts_qs = failed_attempts_qs.filter(ip_address=ip_address)
    if user_agent:
        failed_attempts_qs = failed_attempts_qs.filter(user_agent=user_agent)

    failed_attempts = failed_attempts_qs.count()

    threshold = FAILED_LOGIN_THRESHOLD if failed_type=="login" else FAILED_OTP_THRESHOLD

    if failed_attempts >= threshold:
        # Check throttle: last alert sent?
        last_alert = getattr(user, f'last_{failed_type}_alert', None)
        if last_alert and (now - last_alert).total_seconds() < ALERT_THROTTLE_MINUTES*60:
            return False  # throttled

        # Construct alert message
        message = (
            f"Alert: {failed_attempts} {alert_prefix} attempts "
            f"for your account within last {WINDOW_MINUTES} minutes."
        )

        # Send SMS if available
        if user.phone_number:
            send_sms_task.delay(user.phone_number, message)

        # Send Email
        if user.email:
            send_email_task.delay(
                user.email,
                f"Security Alert: Multiple {alert_prefix.title()}s",
                message
            )

        # Optionally: log for admin dashboard / internal monitoring
        print(f"[SECURITY ALERT] {message} - user {user.email}")

        # Update last alert timestamp to throttle future alerts
        setattr(user, f'last_{failed_type}_alert', now)
        user.save(update_fields=[f'last_{failed_type}_alert'])

        return True

    return False