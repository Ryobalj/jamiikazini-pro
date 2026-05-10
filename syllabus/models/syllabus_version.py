# jamiikazini/syllabus/models/syllabus_version.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel
from django.utils.translation import gettext_lazy as _


class SyllabusVersion(UUIDModel, TimeStampedModel):
    """
    Represents a specific version of the syllabus for a given year.
    """

    year = models.PositiveIntegerField(unique=True)

    evaluation_aid = models.TextField(
        blank=True,
        verbose_name=_("Evaluation Aid"),
        help_text=_("Maelezo kuhusu vifaa au njia za evaluation. Mfano: 'Quiz, Assignment, Class Observation.'")
    )

    is_current = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Syllabus Version"
        verbose_name_plural = "Syllabus Versions"
        ordering = ["-year"]

    def __str__(self):
        return f"Syllabus {self.year}{' (current)' if self.is_current else ''}"

    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one syllabus version is current at a time
            SyllabusVersion.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)
  