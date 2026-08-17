# syllabus/models/student.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.class_level import ClassLevel


class Student(UUIDModel, TimeStampedModel):
    class Gender(models.TextChoices):
        MALE = "M", _("Mvulana")
        FEMALE = "F", _("Msichana")

    workstation = models.ForeignKey(
        TeacherWorkStation,
        on_delete=models.CASCADE,
        related_name="students",
        verbose_name=_("Kituo cha Mwalimu"),
        help_text=_("Shule/mwalimu aliyemsajili mwanafunzi huyu."),
    )
    class_level = models.ForeignKey(
        ClassLevel,
        on_delete=models.CASCADE,
        related_name="students",
        verbose_name=_("Darasa"),
    )
    full_name = models.CharField(max_length=255, verbose_name=_("Jina la Mwanafunzi"))
    gender = models.CharField(max_length=1, choices=Gender.choices, verbose_name=_("Jinsia"))
    admission_number = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_("Namba ya Usajili"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Anaendelea na Masomo"))

    class Meta:
        verbose_name = _("Mwanafunzi")
        verbose_name_plural = _("Wanafunzi")
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.class_level.name})"
