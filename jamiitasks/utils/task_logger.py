# jamiitasks/utils/task_logger.py

"""
Centralized task logger for Celery + Django.
Combines TaskLog (for internal tracking) and AuditLog (for global observability).
"""

import logging
from datetime import datetime
from django.utils import timezone

from payments.models.audit_log import AuditLog, AuditAction
from jamiitasks.models import TaskLog

logger = logging.getLogger(__name__)


class TaskLogger:
    """
    Unified logging helper for Celery tasks.
    - Creates TaskLog entries for internal visibility
    - Creates AuditLog entries for enterprise traceability
    """

    @staticmethod
    def log(task_name: str, status: str, desc: str = "", ref: str = None, task_id: str = None, metadata: dict = None):
        """
        Records both TaskLog + AuditLog safely.
        - task_name: Celery task name
        - status: e.g., STARTED, SUCCESS, FAILED, RETRYING, SKIPPED
        - desc: short description or details
        - ref: optional external reference (e.g., transaction ID)
        - task_id: Celery task_id (UUID)
        - metadata: optional extra data (dict)
        """
        timestamp = timezone.now()

        # ================================
        # 1️⃣ TaskLog (if model exists)
        # ================================
        try:
            if TaskLog:
                TaskLog.objects.create(
                    task_name=task_name,
                    status=status,
                    details=desc,
                    reference=ref,
                    task_id=task_id,
                    created_at=timestamp,
                )
        except Exception as e:
            logger.warning(f"[TaskLogger] Failed to write TaskLog for {task_name}: {e}")

        # ================================
        # 2️⃣ AuditLog (encrypted)
        # ================================
        try:
            action_map = {
                "STARTED": AuditAction.CREATE,
                "SUCCESS": AuditAction.UPDATE,
                "FAILED": AuditAction.PAYMENT_RETRY,
                "RETRYING": AuditAction.PAYMENT_RETRY,
                "SKIPPED": AuditAction.OTHER,
                "NOT_FOUND": AuditAction.OTHER,
            }

            AuditLog.log_action(
                user=None,
                action=action_map.get(status.upper(), AuditAction.OTHER),
                description=f"[{task_name}] {status} - {desc}",
                metadata={
                    "reference": ref,
                    "task_id": task_id,
                    "timestamp": str(timestamp),
                    "metadata": metadata or {},
                },
            )
        except Exception as e:
            logger.error(f"[TaskLogger] Failed to record AuditLog for {task_name}: {e}")

        # ================================
        # 3️⃣ Console logger
        # ================================
        level = (
            logging.INFO if status in ["STARTED", "SUCCESS", "SKIPPED"] else logging.WARNING
            if status in ["RETRYING", "NOT_FOUND"]
            else logging.ERROR
        )
        logger.log(level, f"[{task_name}] {status} → {desc}")

        return {
            "task_name": task_name,
            "status": status,
            "description": desc,
            "reference": ref,
            "task_id": task_id,
            "timestamp": timestamp,
        }