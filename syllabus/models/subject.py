# jamiikazini/syllabus/models/subject.py

from django.db import models
from kiini.models.base import TimeStampedModel, UUIDModel

class Subject(UUIDModel, TimeStampedModel):
    """
    Represents an individual subject in the curriculum.
    """

    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    periods_per_week = models.PositiveSmallIntegerField(default=1, help_text="Number of periods per week for this subject")

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.code:
            prefix = "JSS"
            last_subject = Subject.objects.filter(code__startswith=prefix).order_by("-code").first()
            if last_subject and last_subject.code[3:].isdigit():
                last_number = int(last_subject.code[3:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.code = f"{prefix}{new_number:03d}"
        super().save(*args, **kwargs)