# jamiitasks/utils/throttling.py

from functools import wraps
from jamiitasks.services.rate_limiter import TaskRateLimiter
import logging

from jamiitasks.models import TaskLog

logger = logging.getLogger(__name__)


def throttled_task(limit=None, period=None, rate_limit=None, redis_key=None):
    """
    Decorator ya kudhibiti idadi ya Celery tasks kwa kipindi fulani.
    Ina-support formats zote:
      - throttled_task(limit=10, period=60)
      - throttled_task(rate_limit="1/h", redis_key="key_name")
    """
    # 👇 Parse rate_limit kama ipo (mf. "1/h", "5/m", "10/s")
    if rate_limit:
        qty, unit = rate_limit.split("/")
        qty = int(qty)
        unit = unit.lower().strip()
        if unit.startswith("h"):
            period = 3600
        elif unit.startswith("m"):
            period = 60
        elif unit.startswith("s"):
            period = 1
        elif unit.startswith("d"):
            period = 86400
        limit = qty

    from jamiitasks.services.rate_limiter import TaskRateLimiter
    limiter = TaskRateLimiter(limit=limit or 10, period=period or 60)

    def decorator(fn):
        from functools import wraps
        import logging
        logger = logging.getLogger(__name__)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not limiter.allow(redis_key or fn.__name__):
                logger.warning(f"⛔ Task {fn.__name__} throttled — too many calls")
                from jamiitasks.models import TaskLog
                TaskLog.record(fn.__name__, "THROTTLED", details="Too many calls", reference=redis_key)
                return None
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def log_task_event(task_name, status, details="", reference=None):
    """Record a lightweight event for a throttled task."""
    try:
        TaskLog.record(task_name, status, details=details, reference=reference)
    except Exception as e:
        logger.warning(f"Failed to log task event: {e}")
