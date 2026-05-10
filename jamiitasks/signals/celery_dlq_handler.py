# jamiitasks/signals/celery_dlq_handler.py

from celery.signals import task_failure
from jamiitasks.services.dead_letter_service import DeadLetterService
import traceback

@task_failure.connect
def global_task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, einfo=None, **extras):
    """
    Automatically log any failed Celery task into the Dead Letter Queue.
    """
    tb = einfo.traceback if einfo else traceback.format_exc()
    DeadLetterService().push(
        task_name=sender.name if sender else "unknown",
        task_id=task_id,
        payload={"args": args, "kwargs": kwargs},
        error=str(exception),
        traceback=tb,
        attempts=getattr(sender, "max_retries", 0),
        metadata={"alert_on_fail": True, "source": "celery_signal"}
    )
