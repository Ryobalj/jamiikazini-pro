# jamiitasks/models/task_log.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import TimeStampedModel

class TaskLog(TimeStampedModel):
    """
    Lightweight log for Celery tasks — complementary to AuditLog.
    """
    task_name = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=50, db_index=True)
    details = models.TextField(blank=True)
    retries = models.PositiveIntegerField(default=0)
    duration_ms = models.FloatField(null=True, blank=True, help_text=_("Execution duration in milliseconds"))
    worker_id = models.CharField(max_length=100, blank=True, null=True, help_text=_("Celery worker hostname"))
    task_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    reference = models.CharField(max_length=255, blank=True, null=True, help_text=_("External reference e.g. transaction ref"))

    class Meta:
        verbose_name = _("Task Log")
        verbose_name_plural = _("Task Logs")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.task_name} [{self.status}]"

    @staticmethod
    def record(task_name, status, details="", retries=0, reference=None, worker_id=None, task_id=None, duration_ms=None):
        """
        Simple static method to log a task event quickly.
        """
        return TaskLog.objects.create(
            task_name=task_name,
            status=status,
            details=details,
            retries=retries,
            reference=reference,
            worker_id=worker_id,
            task_id=task_id,
            duration_ms=duration_ms,
        )
