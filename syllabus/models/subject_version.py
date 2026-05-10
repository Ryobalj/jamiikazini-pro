# jamiikazini/syllabus/models/subject_version.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel

class SubjectVersion(UUIDModel, TimeStampedModel):
    """
    Represents a specific version of a subject for a given syllabus
    and class level.
    """

    syllabus_version = models.ForeignKey(
        "syllabus.SyllabusVersion",
        on_delete=models.CASCADE,
        related_name="subject_versions"
    )
    subject = models.ForeignKey(
        "syllabus.Subject",
        on_delete=models.CASCADE,
        related_name="versions"
    )
    class_level = models.ForeignKey(
        "syllabus.ClassLevel",
        on_delete=models.CASCADE,
        related_name="subject_versions"
    )

    # -------------------------
    # NEW BOOLEAN FIELDS
    # -------------------------
    is_english = models.BooleanField(
        default=False,
        help_text="Marks if this subject version belongs to the English-medium syllabus"
    )
    is_awali = models.BooleanField(
        default=False,
        help_text="Marks if this subject version is for Awali curriculum"
    )

    order = models.PositiveIntegerField(
        help_text="Order of subjects within syllabus_version + class_level",
        editable=False,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Subject Version"
        verbose_name_plural = "Subject Versions"
        ordering = [
            "syllabus_version__year",
            "class_level__order",
            "order",
        ]
        unique_together = ("syllabus_version", "subject", "class_level")

    def save(self, *args, **kwargs):
        if self.order is None:
            max_order = SubjectVersion.objects.filter(
                syllabus_version=self.syllabus_version,
                class_level=self.class_level
            ).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.subject.name} ({self.class_level.name}) - "
            f"{self.syllabus_version.year}"
        )