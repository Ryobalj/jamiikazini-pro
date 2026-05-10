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
from jamiitasks.config.throttling import apply_throttling

print("🚀 [Jamiitasks] Initializing Celery task throttling system...")
apply_throttling()