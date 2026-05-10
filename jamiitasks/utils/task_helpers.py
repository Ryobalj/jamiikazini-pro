# jamiitasks/utils/task_helpers.py

from functools import wraps
from jamiitasks.services.dead_letter_service import DeadLetterService
import logging

logger = logging.getLogger(__name__)

def with_dlq(max_retries=3):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            attempts = kwargs.pop("_attempts", 0)
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                attempts += 1
                if attempts >= max_retries:
                    try:
                        ds = DeadLetterService()
                        ds.push(
                            task_name=getattr(fn, "__name__", str(fn)),
                            task_id=None,
                            payload={"args": args, "kwargs": kwargs},
                            error=str(e),
                            traceback=None,
                            attempts=attempts,
                        )
                    except Exception:
                        logger.exception("Failed to push to DLQ")
                    raise  # re-raise so Celery marks it failed
                else:
                    # Re-raise or retry via Celery (this decorator is for sync functions)
                    raise
        return wrapper
    return decorator