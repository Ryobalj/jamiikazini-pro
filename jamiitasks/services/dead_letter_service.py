# jamiitasks/services/dead_letter_service.py

import logging
from django.utils import timezone
from jamiitasks.models.dead_letter import DeadLetterQueue

logger = logging.getLogger(__name__)

class DeadLetterService:
    def __init__(self):
        pass

    def push(self, task_name: str, task_id: str = None, payload: dict = None,
             error: str = None, traceback: str = None, attempts: int = 0, metadata: dict = None):
        """
        Create a DeadLetterQueue record. Keep payload + metadata small (or store large blobs in S3 and put ref).
        """
        try:
            dl = DeadLetterQueue.objects.create(
                task_name=task_name,
                task_id=task_id,
                payload=payload or {},
                error=error or "",
                traceback=traceback or "",
                attempts=attempts or 0,
                last_attempt_at=timezone.now(),
                metadata=metadata or {},
            )
            # Optionally send alert for certain tasks
            if metadata and metadata.get("alert_on_fail"):
                try:
                    from security.helpers.alerts import send_slack_alert
                    send_slack_alert(f"[DLQ] task={task_name} id={dl.id} attempts={attempts} meta={metadata}")
                except Exception:
                    logger.exception("Failed to send DLQ alert")
            return dl
        except Exception:
            logger.exception("Failed to persist dead letter")
            raise

    def requeue(self, dead_letter: DeadLetterQueue):
        """
        Re-queue logic:
         - Put original payload back to Celery with same task name (best-effort).
         - Mark DLQ entry as requeued.
         - In production you might want to implement backoff & dedup.
        """
        from celery import current_app
        # pick queue / routing if available in metadata
        try:
            # If metadata contains routing info or kwargs names, use them
            payload = dead_letter.payload or {}
            task = current_app.tasks.get(dead_letter.task_name)
            if not task:
                # fallback: try direct send_task
                current_app.send_task(dead_letter.task_name, args=payload.get("args", []), kwargs=payload.get("kwargs", {}))
            else:
                # call apply_async with same retry policy
                task.apply_async(args=payload.get("args", []), kwargs=payload.get("kwargs", {}))
            dead_letter.mark_requeued()
            return True
        except Exception:
            logger.exception("Failed to requeue dead letter %s", dead_letter.id)
            return False