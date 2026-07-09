# jamiitasks/tasks/__init__.py

"""
Jamiitasks entrypoint — registers all Celery tasks
and applies dynamic throttling automatically at worker startup.
"""

# ==========================
# ✅ Import all task modules
# ==========================
from jamiitasks.tasks.payments_gateway_tasks import *
from jamiitasks.tasks.payment_tasks import *
from jamiitasks.tasks.distributed_payment_tasks import *
from jamiitasks.tasks.exchange_rate_tasks import *
from jamiitasks.tasks.test_tasks import *
from jamiitasks.tasks.cleanup import *
from jamiitasks.tasks.messaging import *
from jamiitasks.tasks.notifications import *
from jamiitasks.tasks.wallet import *
from jamiitasks.tasks.security_tasks import *

# ==========================
# ⚙️ Apply Dynamic Throttling
# ==========================
# NB: apply_throttling() hutuma broadcast kwa broker (Redis). Lazima IENDESHWE
# TU ndani ya Celery worker — SI wakati wa web/Django startup. Module hii huimport-
# iwa na URLconf (security.urls -> notifications), kwa hivyo bila kizuizi hiki
# kila HTTP request ingejaribu Redis na kukwamisha gunicorn worker (timeout -> 500).
import os as _os
import sys as _sys

from jamiitasks.config.throttling import apply_throttling

_argv = " ".join(_sys.argv).lower()
_is_celery_worker = "celery" in _argv and "worker" in _argv
_force = _os.getenv("JAMII_APPLY_THROTTLING", "").lower() in ("1", "true", "yes")

if _is_celery_worker or _force:
    print("🚀 [Jamiitasks] Initializing Celery task throttling system...")
    apply_throttling()