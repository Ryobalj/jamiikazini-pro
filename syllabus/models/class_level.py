# jamiikazini/syllabus/models/class_level.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel

class ClassLevel(UUIDModel, TimeStampedModel):
    """
    Represents a school class/grade level, e.g., 'III', 'IV', 'V', 'VI'.
    """

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(
        help_text="Ordering of class levels, auto-incremented",
        editable=False,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Class Level"
        verbose_name_plural = "Class Levels"
        ordering = ["order"]

    def save(self, *args, **kwargs):
        if self.order is None:
            # Pata max order iliyopo na ongeza 1
            max_order = ClassLevel.objects.aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name