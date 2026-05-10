# jamiikazini/celery.py

import os
from celery import Celery
import logging

logger = logging.getLogger(__name__)

# ==========================
# 🌍 Environment Setup
# ==========================
os.environ.setdefault("DJANGO_ENV", "dev")
ENVIRONMENT = os.environ["DJANGO_ENV"]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"jamiikazini.settings.{ENVIRONMENT}")

# ==========================
# 🚀 Initialize Celery App
# ==========================
app = Celery("jamiikazini")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.enable_utc = True
app.conf.timezone = "Africa/Nairobi"

# ==========================
# 🔍 Explicit Task Discovery
# ==========================
# Tunataja moja kwa moja modules zote ndani ya jamiitasks
app.autodiscover_tasks([
    "jamiitasks",
    "jamiitasks.tasks",
    "jamiitasks.tasks.payment_tasks",
    "jamiitasks.tasks.distributed_payment_tasks",
    "jamiitasks.tasks.payments_gateway_tasks",
    "jamiitasks.tasks.wallet",
    "jamiitasks.tasks.cleanup",
    "jamiitasks.tasks.messaging",
    "jamiitasks.tasks.notifications",
    "jamiitasks.tasks.exchange_rate_tasks",
    "jamiitasks.tasks.test_tasks",
    "jamiitasks.tasks.security_tasks",

])

logger.info(f"✅ Celery started with settings: jamiikazini.settings.{ENVIRONMENT}")

# ==========================
# 🎯 Optional Debugging
# ==========================
@app.task(bind=True)
def debug_task(self):
    logger.info(f"Request: {self.request!r}")