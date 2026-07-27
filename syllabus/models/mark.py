# syllabus/models/mark.py

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel
from syllabus.models.exam import Exam
from syllabus.models.student import Student
from syllabus.models.subject import Subject


class Mark(UUIDModel, TimeStampedModel):
    """Alama za mwanafunzi mmoja kwenye somo moja, kwa mtihani mmoja."""

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="marks", verbose_name=_("Mtihani"))
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="marks", verbose_name=_("Mwanafunzi"))
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="marks", verbose_name=_("Somo"))
    score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Alama"),
    )

    class Meta:
        verbose_name = _("Alama")
        verbose_name_plural = _("Alama")
        unique_together = ("exam", "student", "subject")
        ordering = ["student", "subject"]

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name}: {self.score}"
