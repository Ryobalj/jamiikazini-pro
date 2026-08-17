# syllabus/models/exam.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.class_level import ClassLevel
from syllabus.models.subject import Subject


class Exam(UUIDModel, TimeStampedModel):
    """Mtihani/upimaji mmoja kwa darasa fulani - mfano 'Upimaji wa Nusu
    Muhula' kwa STD III, Muhula wa Kwanza 2026. Alama za kila somo
    zinapimwa kati ya 0 na max_score_per_subject (kawaida 50, kama
    ilivyo kwenye taarifa rasmi za TAMISEMI)."""

    class Term(models.IntegerChoices):
        FIRST = 1, _("Muhula wa Kwanza")
        SECOND = 2, _("Muhula wa Pili")

    workstation = models.ForeignKey(
        TeacherWorkStation,
        on_delete=models.CASCADE,
        related_name="exams",
        verbose_name=_("Kituo cha Mwalimu"),
    )
    class_level = models.ForeignKey(
        ClassLevel,
        on_delete=models.CASCADE,
        related_name="exams",
        verbose_name=_("Darasa"),
    )
    subjects = models.ManyToManyField(
        Subject,
        related_name="exams",
        verbose_name=_("Masomo"),
        help_text=_("Masomo yanayohusika kwenye mtihani huu."),
    )
    name = models.CharField(
        max_length=255,
        default="Upimaji wa Nusu Muhula",
        verbose_name=_("Jina la Mtihani"),
    )
    term = models.IntegerField(choices=Term.choices, default=Term.FIRST, verbose_name=_("Muhula"))
    year = models.PositiveIntegerField(verbose_name=_("Mwaka"))
    max_score_per_subject = models.PositiveIntegerField(
        default=50, verbose_name=_("Alama za Juu kwa Somo"),
    )

    class Meta:
        verbose_name = _("Mtihani")
        verbose_name_plural = _("Mitihani")
        ordering = ["-year", "-term"]

    def __str__(self):
        return f"{self.name} - {self.class_level.name} ({self.get_term_display()} {self.year})"
