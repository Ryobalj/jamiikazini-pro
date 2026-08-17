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
    # Nukuu za Somo follows a real teaching flow, not one undifferentiated
    # block of text: (1) introduction — meaning/concept, (2) further
    # details — explains the concept in depth, (3) mifano — worked
    # examples illustrating the concept itself, (4) daily-life uses —
    # where the concept shows up day-to-day — then the exercise
    # (exercise_questions) closes the flow.
    lesson_notes_intro = models.TextField(
        blank=True,
        default="",
        help_text="Utangulizi — the meaning and concept of the topic"
    )
    lesson_notes_details = models.TextField(
        blank=True,
        default="",
        help_text="Maelezo zaidi — explains the concept in depth (types/parts, only if it has several)"
    )
    lesson_notes_illustrations = models.TextField(
        blank=True,
        default="",
        help_text="Mifano — worked examples illustrating the concept itself"
    )
    lesson_notes_daily_life = models.TextField(
        blank=True,
        default="",
        help_text="Matumizi ya kila siku — real-life applications of this concept"
    )
    exercise_questions = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Practice exercise for this activity: a list of "
            "{'question': str, 'answer': str} objects, at least 3. "
            "'answer' holds the worked solution for computational questions."
        )
    )
    DIAGRAM_CHOICES = [
        ("", "None"),
        ("roman_numerals_chart", "Roman numerals value chart"),
        ("unit_conversion_ladder", "Unit conversion ladder (km/m/cm etc.)"),
        ("rectangle_diagram", "Labelled rectangle/square (perimeter & area)"),
        ("fraction_bar", "Fraction bar comparison"),
        ("clock_face", "Clock face"),
        ("place_value_chart", "Decimal place-value chart"),
    ]
    diagram_type = models.CharField(
        max_length=32,
        choices=DIAGRAM_CHOICES,
        blank=True,
        default="",
        help_text="Which illustrative diagram (drawn programmatically, no image upload needed) to show in the Nukuu za Somo document, if any."
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