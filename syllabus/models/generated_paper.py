# syllabus/models/generated_paper.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel


class GeneratedPaper(UUIDModel, TimeStampedModel):
    """One persisted instance of a randomly-assembled quiz/test/examination.
    Persisted (not recomputed on each request, unlike Scheme of Work /
    Lesson Plan) so the paper and its answer key stay consistent across
    repeat downloads."""

    exam_format = models.ForeignKey(
        "syllabus.ExamFormat", on_delete=models.PROTECT, related_name="generated_papers"
    )
    subject_version = models.ForeignKey(
        "syllabus.SubjectVersion", on_delete=models.CASCADE, related_name="generated_papers"
    )
    workstation = models.ForeignKey(
        "syllabus.TeacherWorkStation", on_delete=models.CASCADE, related_name="generated_papers"
    )
    title = models.CharField(max_length=255, blank=True, default="")
    year = models.PositiveIntegerField(null=True, blank=True)
    term = models.PositiveIntegerField(null=True, blank=True)
    seed = models.CharField(
        max_length=64, blank=True, default="", help_text="Random seed used, for reproducibility."
    )

    class Meta:
        verbose_name = "Generated Paper"
        verbose_name_plural = "Generated Papers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title or self.exam_format.name} - {self.subject_version}"


class GeneratedPaperQuestion(UUIDModel, TimeStampedModel):
    """Through table: which questions, in which order/section, and at what
    marks weight (snapshotted from the slot at generation time, independent
    of the question's own default marks) make up a given GeneratedPaper."""

    generated_paper = models.ForeignKey(
        GeneratedPaper, on_delete=models.CASCADE, related_name="paper_questions"
    )
    question = models.ForeignKey(
        "syllabus.Question", on_delete=models.PROTECT, related_name="paper_appearances"
    )
    section_name = models.CharField(max_length=100)
    order_in_section = models.PositiveIntegerField(default=1)
    marks = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Generated Paper Question"
        verbose_name_plural = "Generated Paper Questions"
        ordering = ["generated_paper", "section_name", "order_in_section"]

    def __str__(self):
        return f"{self.generated_paper} - Q{self.order_in_section} ({self.section_name})"
