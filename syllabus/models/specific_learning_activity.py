# jamiikazini/syllabus/models/specific_learning_activity.py

from django.db import models
from django.contrib.postgres.fields import ArrayField
from kiini.models.base import UUIDModel, TimeStampedModel

class SpecificLearningActivity(UUIDModel, TimeStampedModel):
    """
    Represents a specific learning activity detail under a learning activity.
    """

    learning_activity = models.ForeignKey(
        "syllabus.LearningActivity",
        on_delete=models.CASCADE,
        related_name="specific_activities"
    )
    method = models.TextField(
        help_text="Teaching method or approach"
    )

    leading = ArrayField(
        base_field=models.TextField(),
        blank=True,
        null=True,
        default=list,
        help_text="Specific learning tasks or exercises (unaweza kuongeza nyingi)"
    )

    name = models.TextField(
        help_text="Specific learning tasks or exercises"
    )
    assessment_criteria = models.TextField(
        help_text="Criteria for evaluating the activity"
    )
    teaching_aids = ArrayField(
        base_field=models.TextField(),
        blank=True,
        null=True,
        default=list,
        help_text="Teaching aids or materials used (unaweza kuongeza nyingi)"
    )
    references = ArrayField(
        base_field=models.TextField(),
        blank=True,
        null=True,
        default=list,
        help_text="References or sources (unaweza kuongeza nyingi)"
    )
    periods = models.PositiveIntegerField(
        default=1,
        help_text="Number of periods allocated for this activity"
    )
    order = models.PositiveIntegerField(
        editable=False,
        blank=True,
        null=True,
        help_text="Order within the parent learning activity"
    )

    class Meta:
        verbose_name = "Specific Learning Activity"
        verbose_name_plural = "Specific Learning Activities"
        ordering = ["learning_activity", "order"]
        unique_together = ("learning_activity", "name")

    def save(self, *args, **kwargs):
        if self.order is None:
            max_order = SpecificLearningActivity.objects.filter(
                learning_activity=self.learning_activity
            ).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name[:50]}... ({self.learning_activity})"