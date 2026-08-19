# syllabus/models/exam_format.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel

from syllabus.models.question import Question


class ExamFormat(UUIDModel, TimeStampedModel):
    """A reusable template describing the shape of a quiz/test/examination:
    its sections, the question-type/difficulty/count mix within each
    section, timing and instructions. Derived from real exam papers as
    format-structure references (see ExamFormatSection/ExamFormatSlot) -
    never a source of question content itself."""

    class PaperType(models.TextChoices):
        QUIZ = "quiz", "Quiz"
        TEST = "test", "Test"
        EXAMINATION = "examination", "Examination"

    name = models.CharField(
        max_length=255, help_text="e.g. 'Std VII Maarifa ya Jamii Mock Format'"
    )
    paper_type = models.CharField(max_length=20, choices=PaperType.choices)
    subject = models.ForeignKey(
        "syllabus.Subject",
        on_delete=models.CASCADE,
        related_name="exam_formats",
        null=True,
        blank=True,
        help_text="Leave blank for a generic format reusable across subjects.",
    )
    class_level = models.ForeignKey(
        "syllabus.ClassLevel",
        on_delete=models.CASCADE,
        related_name="exam_formats",
        null=True,
        blank=True,
        help_text="Leave blank for a generic format reusable across class levels.",
    )
    time_allowed_minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Total time allowed, in minutes (e.g. 90 for 'Saa 1:30')."
    )
    instructions = models.TextField(
        blank=True,
        default="",
        help_text="Free-text 'Maelekezo'/'Instructions' block, one numbered rule per line.",
    )
    total_marks = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Sum of all sections' marks - kept in sync by recompute_total_marks().",
    )
    is_active = models.BooleanField(default=True)
    is_custom = models.BooleanField(
        default=False,
        help_text=(
            "True if a teacher built this format ad-hoc for one generation "
            "(the 'manual' paper-builder flow), rather than an admin-curated "
            "library template. Custom formats are excluded from the "
            "browsable format list - they exist only so generation can "
            "reuse the normal ExamFormat/Section/Slot pipeline."
        ),
    )
    created_by_workstation = models.ForeignKey(
        "syllabus.TeacherWorkStation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="custom_exam_formats",
        help_text="Set only for is_custom=True formats.",
    )

    class Meta:
        verbose_name = "Exam Format"
        verbose_name_plural = "Exam Formats"
        ordering = ["paper_type", "name"]

    def recompute_total_marks(self):
        total = 0
        for section in self.sections.all():
            for slot in section.slots.all():
                total += slot.count * slot.marks_per_item
        self.total_marks = total
        self.save(update_fields=["total_marks"])

    def __str__(self):
        return f"{self.name} ({self.get_paper_type_display()})"


class ExamFormatSection(UUIDModel, TimeStampedModel):
    exam_format = models.ForeignKey(ExamFormat, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=100, help_text="e.g. 'SEHEMU A' / 'SECTION A'")
    order = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Exam Format Section"
        verbose_name_plural = "Exam Format Sections"
        ordering = ["exam_format", "order"]
        unique_together = ("exam_format", "name")

    def __str__(self):
        return f"{self.name} ({self.exam_format.name})"


class ExamFormatSlot(UUIDModel, TimeStampedModel):
    """One 'N questions of type X, difficulty Y, worth Z marks each' rule
    within a section. A section is just an ordered list of slots - this is
    what lets one format reproduce a real exam's exact heterogeneous
    structure (e.g. 15 MCQ + 5 matching in one section, mixed short-answer
    /calculation in another) without hardcoding per-subject logic."""

    section = models.ForeignKey(ExamFormatSection, on_delete=models.CASCADE, related_name="slots")
    order = models.PositiveIntegerField(default=1)
    question_type = models.CharField(max_length=20, choices=Question.QuestionType.choices)
    difficulty = models.CharField(
        max_length=10, choices=Question.Difficulty.choices, default=Question.Difficulty.MEDIUM
    )
    count = models.PositiveIntegerField(
        default=1, help_text="How many questions of this type/difficulty to pick."
    )
    marks_per_item = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Exam Format Slot"
        verbose_name_plural = "Exam Format Slots"
        ordering = ["section", "order"]

    def __str__(self):
        return f"{self.count} x {self.get_question_type_display()} ({self.difficulty}) @ {self.marks_per_item}pts"
