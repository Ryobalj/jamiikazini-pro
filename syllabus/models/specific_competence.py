# jamiikazini/syllabus/models/specific_competence.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel

class SpecificCompetence(UUIDModel, TimeStampedModel):
    """
    Represents a specific competence under a main competence.
    """

    main_competence = models.ForeignKey(
        "syllabus.MainCompetence",
        on_delete=models.CASCADE,
        related_name="specific_competences"
    )
    name = models.TextField(
        help_text="Description of the specific competence"
    )
    order = models.PositiveIntegerField(
        help_text="Order of specific competences within a MainCompetence",
        editable=False,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Specific Competence"
        verbose_name_plural = "Specific Competences"
        ordering = ["main_competence", "order"]
        unique_together = ("main_competence", "name")

    def save(self, *args, **kwargs):
        if self.order is None:
            max_order = SpecificCompetence.objects.filter(
                main_competence=self.main_competence
            ).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name[:50]}... ({self.main_competence})"