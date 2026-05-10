# jamiitasks/services/notification_gateway.py

import logging
from django.contrib.auth import get_user_model

from jamiitasks.services.push_gateway import send_push
from jamiitasks.services.email_gateway import send_email

logger = logging.getLogger(__name__)
User = get_user_model()

def notify_new_message(user_id, message="Una ujumbe mpya kwenye Jamiikazini"):
    """
    Tuma notification kwa mtumiaji kuwa ana ujumbe mpya.
    Inaweza kuwa push notification au email, kulingana na uwezo wa user.
    """
    try:
        user = User.objects.get(id=user_id)
        contact_methods = []

        # Jaribu kutuma push notification
        if getattr(user, 'device_token', None):
            try:
                push_response = send_push(
                    user_id=user.id,
                    message=message,
                    device_token=user.device_token,
                    title="Ujumbe Mpya"
                )
                if push_response["status"] == "success":
                    logger.info(f"[Notify] Push imetumwa kwa {user.username}")
                    return {"status": "success", "method": "push"}
                else:
                    logger.warning(f"[Notify] Push ilishindikana: {push_response}")
                contact_methods.append("push_failed")

            except Exception as e:
                logger.error(f"[Notify] Hitilafu kwenye push kwa {user.username}: {e}")
                contact_methods.append("push_error")

        # Ikiwa push haikufanikiwa au haipo, jaribu email
        if user.email:
            try:
                email_response = send_email(
                    subject="Ujumbe Mpya",
                    message=message,
                    recipient=user.email
                )
                logger.info(f"[Notify] Email imetumwa kwa {user.email}")
                return {"status": "success", "method": "email"}
            except Exception as e:
                logger.error(f"[Notify] Hitilafu kwenye email kwa {user.email}: {e}")
                contact_methods.append("email_error")

        logger.warning(f"[Notify] Hakuna njia ya kuwasiliana na mtumiaji {user.username}.")
        return {"status": "failed", "reason": "No working contact method", "attempted": contact_methods}

    except User.DoesNotExist:
        logger.error(f"[Notify] User na ID={user_id} haipatikani.")
        return {"status": "failed", "reason": "User not found"}

    except Exception as e:
        logger.error(f"[Notify] Hitilafu isiyotegemewa: {e}")
        return {"status": "error", "message": str(e)}