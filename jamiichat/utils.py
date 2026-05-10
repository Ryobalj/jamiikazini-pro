# jamiichat/utils.py

from jamiitasks.tasks.messaging import send_chat_message_task

def send_chat_message(user, content):
    """
    Send chat message asynchronously using Celery task.
    """
    # Kwa sasa, tunatumia user.id kama recipient_id, na sender_id = None au system user (e.g. 0)
    sender_id = None  # au user system id ikiwa ipo
    recipient_id = user.id

    # Kuita task ya kutuma message (async)
    send_chat_message_task.delay(sender_id, recipient_id, content)