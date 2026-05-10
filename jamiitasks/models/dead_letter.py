# jamiitasks/models/dead_letter.py

from django.db import models
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel

class DeadLetterQueue(UUIDModel, TimeStampedModel):
    """
    Records failed background jobs/tasks that exceeded retry policy or failed fatally.
    Keep structured metadata to allow replay / manual inspection.
    """
    TASK_STATUS_CHOICES = [
        ("FAILED", "Failed"),
        ("RETRY_EXHAUSTED", "Retry exhausted"),
        ("MANUAL_PAUSED", "Manual paused"),
    ]

    task_name = models.CharField(max_length=255, db_index=True)
    task_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)   # input arguments / kwargs
    error = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)
    attempts = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=TASK_STATUS_CHOICES, default="FAILED")
    metadata = models.JSONField(default=dict, blank=True)  # gateway, invoice id, user, idempotency_key, etc.
    requeued = models.BooleanField(default=False)
    requeued_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "jamiitasks_deadletterqueue"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task_name"]),
            models.Index(fields=["task_id"]),
            models.Index(fields=["status"]),
        ]

    def mark_requeued(self):
        self.requeued = True
        self.requeued_at = timezone.now()
        self.status = "MANUAL_PAUSED"
        self.save(update_fields=["requeued", "requeued_at", "status"])