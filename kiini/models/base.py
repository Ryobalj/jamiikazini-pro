# kiini/models/base.py

from django.db import models
from django.utils import timezone
import uuid


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    @property
    def created(self):
        return self.created_at

    @property
    def updated(self):
        return self.updated_at

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
