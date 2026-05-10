# jamiitasks/services/messaging_gateway.py

import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.apps import apps
from django.db import transaction
import time

logger = logging.getLogger(__name__)

User = get_user_model()
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2  # Kuchelewesha retries kidogo

def send_chat_message(sender_id, recipient_id, message_text, retries=0):
    """
    Hifadhi ujumbe kwenye database kupitia model ya Message, 
    na toa nafasi ya kutuma push notification au websocket notification.

    Parameters:
    - sender_id: ID ya mtumiaji anayetuma ujumbe
    - recipient_id: ID ya mpokeaji
    - message_text: Maudhui ya ujumbe
    - retries: Idadi ya retries zilizofanyika

    Returns:
    - dict yenye status, message_id na sent_at wakati wa kutuma ujumbe

    Inarudi exception ikiwa retries zote zimefanyika bila mafanikio.
    """

    Message = apps.get_model('jamiichat', 'Message')

    try:
        sender = User.objects.get(id=sender_id)
        recipient = User.objects.get(id=recipient_id)

        with transaction.atomic():
            message = Message.objects.create(
                sender=sender,
                recipient=recipient,
                content=message_text,
                sent_at=timezone.now(),
                status='sent'
            )

        logger.info(f"[Chat] Ujumbe umetumwa kutoka {sender_id} kwenda {recipient_id} (ID: {message.id})")

        # TODO: Ongeza websocket/push notification hapa kwa recipient
        # Example: push_gateway.send_push(recipient.id, "Ujumbe mpya umepokelewa.")

        return {
            'status': 'success',
            'message_id': message.id,
            'sent_at': message.sent_at
        }

    except User.DoesNotExist:
        logger.warning(f"[Chat] Sender au recipient haonekani: sender_id={sender_id}, recipient_id={recipient_id}")
        raise

    except Exception as e:
        logger.error(f"[Chat] Hitilafu kutuma ujumbe: {e} (retry {retries}/{MAX_RETRIES})")

        if retries < MAX_RETRIES:
            logger.info(f"[Chat] Inajaribu tena baada ya kuchelewa sekunde {RETRY_DELAY_SECONDS}...")
            time.sleep(RETRY_DELAY_SECONDS)
            return send_chat_message(sender_id, recipient_id, message_text, retries=retries + 1)

        raise