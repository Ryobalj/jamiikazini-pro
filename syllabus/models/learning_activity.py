# jamiikazini/syllabus/models/learning_activity.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel

class LearningActivity(UUIDModel, TimeStampedModel):
    """
    Represents a learning activity under a specific competence.
    """

    specific_competence = models.ForeignKey(
        "syllabus.SpecificCompetence",
        on_delete=models.CASCADE,
        related_name="learning_activities"
    )
    name = models.TextField(
        help_text="Description of the learning activity"
    )
    order = models.PositiveIntegerField(
        help_text="Order of learning activities within a specific competence",
        editable=False,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Learning Activity"
        verbose_name_plural = "Learning Activities"
        ordering = ["specific_competence", "order"]
        unique_together = ("specific_competence", "name")

    def save(self, *args, **kwargs):
        if self.order is None:
            max_order = LearningActivity.objects.filter(
                specific_competence=self.specific_competence
            ).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name[:50]}... ({self.specific_competence})"