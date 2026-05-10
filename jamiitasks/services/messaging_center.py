# jamiitasks/services/messaging_center.py

import logging
from jamiitasks.services import sms_gateway, email_gateway, push_gateway

logger = logging.getLogger(__name__)


class MessagingCenter:
    def __init__(self):
        self.sms = sms_gateway
        self.email = email_gateway
        self.push = push_gateway

    def send_sms(self, phone, message):
        try:
            return self.sms.send_sms(phone, message)
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return {"status": "failed", "error": str(e)}

    def send_email(self, to_email, subject, body, html_body=None):
        try:
            return self.email.send_email(to_email, subject, body, html_body)
        except Exception as e:
            logger.error(f"Failed to send Email: {str(e)}")
            return {"status": "failed", "error": str(e)}

    def send_push(self, user_id, message, device_token=None, title="JamiiKazini", data=None):
        try:
            return self.push.send_push(user_id, message, device_token, title, data)
        except Exception as e:
            logger.error(f"Failed to send Push Notification: {str(e)}")
            return {"status": "failed", "error": str(e)}

    def send_all(self, *, user, message, subject=None, html_body=None, data=None):
        """
        Tuma ujumbe kwa njia zote: Push, SMS, na Email.
        Lazima `user` awe na field za `email`, `phone`, `device_token`.
        """
        results = {}

        if hasattr(user, 'device_token') and user.device_token:
            results['push'] = self.send_push(user.id, message, user.device_token, title=subject or "Notification", data=data)

        if hasattr(user, 'phone') and user.phone:
            results['sms'] = self.send_sms(user.phone, message)

        if hasattr(user, 'email') and user.email:
            results['email'] = self.send_email(user.email, subject or "Notification", message, html_body=html_body)

        return results