# jamiitasks/config/throttling.py

"""
Dynamic Celery throttling configuration for Jamiikazini EAC infrastructure.

Rate limits are expressed as "<count>/<period>", e.g. "60/m" (60 per minute).
The limits automatically scale based on the number of active workers and concurrency.
"""

import os
from celery import current_app

# ================================
# ⚙️  Base Throttle Definitions
# ================================

BASE_LIMITS = {
    # 🔹 PAYMENT GATEWAY TASKS
    "jamiitasks.tasks.payments_gateway_tasks.initiate_payment": 10,
    "jamiitasks.tasks.payments_gateway_tasks.verify_transaction": 20,
    "jamiitasks.tasks.payments_gateway_tasks.poll_gateway_status": 30,
    "jamiitasks.tasks.payments_gateway_tasks.reconcile_settlements": 5,

    # 🔹 WALLET TASKS
    "jamiitasks.tasks.wallet.confirm_topup_transaction": 25,
    "jamiitasks.tasks.wallet.auto_sync_wallet_balance": 15,
    "jamiitasks.tasks.wallet.process_withdraw_request": 10,
    "jamiitasks.tasks.wallet.retry_failed_wallet_update": 40,

    # 🔹 EXCHANGE RATE TASKS
    "jamiitasks.tasks.exchange_rate_tasks.update_rates_from_source": 1,
    "jamiitasks.tasks.exchange_rate_tasks.cache_rates_snapshot": 2,

    # 🔹 NOTIFICATIONS
    "jamiitasks.tasks.notifications.send_sms_task": 60,
    "jamiitasks.tasks.notifications.send_email_task": 30,
    "jamiitasks.tasks.notifications.push_inapp_notification": 80,
    "jamiitasks.tasks.notifications.broadcast_system_alert": 5,

    # 🔹 MESSAGING
    "jamiitasks.tasks.messaging.send_chat_message": 120,
    "jamiitasks.tasks.messaging.archive_old_conversations": 5,

    # 🔹 CLEANUP
    "jamiitasks.tasks.cleanup.purge_old_logs": 2,
    "jamiitasks.tasks.cleanup.remove_inactive_sessions": 10,

    # 🔹 SECURITY / AUDIT
    "jamiitasks.tasks.security_tasks.run_audit_log_rotation": 2,
    "jamiitasks.tasks.security_tasks.flag_suspicious_login": 15,
    "jamiitasks.tasks.security_tasks.notify_admin_security_event": 10,

    # 🔹 TEST / DEV
    "jamiitasks.tasks.test_tasks.fail_test_task": 5,
}

# ================================
# 🧠  Dynamic Scaling Logic
# ================================

def build_throttle_limits():
    """
    Builds dynamic rate limits by scaling according to active worker pool.
    E.g., if base=60/m and we have 3 workers × concurrency 5 → limit = 900/m
    """
    base_limits = BASE_LIMITS.copy()

    # Read scaling context
    worker_count = int(os.getenv("CELERY_WORKERS", "1"))
    concurrency = int(os.getenv("CELERY_CONCURRENCY", "4"))
    env = os.getenv("ENVIRONMENT", "development").lower()

    scaling_factor = worker_count * concurrency

    limits = {}
    for task_name, base_rate in base_limits.items():
        scaled_rate = base_rate * scaling_factor
        limits[task_name] = f"{scaled_rate}/m"

    # Optional: reduce aggressiveness in dev/testing
    if env in ["dev", "development", "testing"]:
        for k in limits:
            count, period = limits[k].split("/")
            limits[k] = f"{max(1, int(int(count) / 3))}/{period}"

    return limits


# ================================
# 🚀  Auto-Apply at Worker Startup
# ================================

def apply_throttling():
    """Applies rate limits dynamically when Celery worker starts."""
    try:
        limits = build_throttle_limits()
        print("🔄 Applying Celery rate limits dynamically...")
        for task_name, limit in limits.items():
            try:
                current_app.control.rate_limit(task_name, limit)
                print(f"✅ {task_name} → {limit}")
            except Exception as e:
                print(f"⚠️ Could not set rate limit for {task_name}: {e}")
        print("🎯 Throttling rules successfully loaded.")
    except Exception as e:
        print(f"❌ Failed to apply throttling: {e}")


# ================================
# 🧩 Expose for import
# ================================

THROTTLE_LIMITS = build_throttle_limits()