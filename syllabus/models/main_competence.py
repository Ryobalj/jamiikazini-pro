# jamiikazini/syllabus/models/main_competence.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel

class MainCompetence(UUIDModel, TimeStampedModel):
    """
    Represents a main competence associated with a specific SubjectVersion.
    """

    subject_version = models.ForeignKey(
        "syllabus.SubjectVersion",
        on_delete=models.CASCADE,
        related_name="main_competences"
    )
    name = models.TextField(
        help_text="Name/description of the main competence"
    )
    order = models.PositiveIntegerField(
        help_text="Order of main competences within a SubjectVersion",
        editable=False,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Main Competence"
        verbose_name_plural = "Main Competences"
        ordering = ["subject_version", "order"]
        unique_together = ("subject_version", "name")

    def save(self, *args, **kwargs):
        if self.order is None:
            max_order = MainCompetence.objects.filter(
                subject_version=self.subject_version
            ).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name[:50]}... ({self.subject_version})"