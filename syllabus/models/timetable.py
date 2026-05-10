# syllabus/models/time_table.py
from django.db import models
from django.utils import timezone
from kiini.models.base import UUIDModel, TimeStampedModel
from django.utils.translation import gettext_lazy as _
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.subject_version import SubjectVersion

class TimeTable(UUIDModel, TimeStampedModel):
    PERIODS = [(i, i) for i in range(1, 11)]

    workstation = models.ForeignKey(
        TeacherWorkStation,
        on_delete=models.CASCADE,
        related_name="timetables",
        verbose_name=_("Kituo cha Mwalimu"),
        help_text=_("Chagua kituo cha kazi cha mwalimu. Hii itahusisha shule na halmashauri automatically.")
    )
    subject_version = models.ForeignKey(
        SubjectVersion,
        on_delete=models.CASCADE,
        verbose_name=_("Somo (Version)"),
        help_text=_("Chagua toleo la somo litakalofundishwa katika kipindi hiki. Hii inaonyesha darasa na syllabus version.")
    )
    period = models.IntegerField(
        choices=PERIODS,
        default=1,
        verbose_name=_("Kipindi"),
        help_text=_("Chagua kipindi cha siku ambacho somo litafundishwa."),
        null=True, 
        blank=True
    )
    timestart = models.TimeField(
        default=timezone.now,
        verbose_name=_("Muda wa Kuanza"),
        help_text=_("Weka muda wa kuanza wa kipindi."),
        null=True, 
        blank=True
    )
    timefinish = models.TimeField(
        default=timezone.now,
        verbose_name=_("Muda wa Kumaliza"),
        help_text=_("Weka muda wa kuisha wa kipindi."),
        null=True, 
        blank=True
    )
    registeredboys = models.IntegerField(
        blank=True, 
        null=True,
        verbose_name=_("Idadi ya Wavulana"),
        help_text=_("Andika idadi ya wavulana walioandikishwa darasani.")
    )
    registeredgirls = models.IntegerField(
        blank=True, 
        null=True,
        verbose_name=_("Idadi ya Wasichana"),
        help_text=_("Andika idadi ya wasichana walioandikishwa darasani.")
    )
    status = models.BooleanField(
        default=False,
        verbose_name=_("Imehakikishwa"),
        help_text=_("Weka True ikiwa mwalimu amethibitisha ratiba hii.")
    )

    class Meta:
        verbose_name = _("Ratiba ya Mwalimu")
        verbose_name_plural = _("Ratiba za Walimu")
        ordering = ["workstation", "subject_version", "-created_at"]
        # ONDOA UNIQUE TOGETHER - INAWEZA KUSABABISHA MATATIZO NA NULL VALUES
        # unique_together = ("workstation", "subject_version", "period")

    def __str__(self):
        teacher_name = self.workstation.teacher.get_full_name() if self.workstation.teacher else "Unknown"
        class_level = self.subject_version.class_level.name if self.subject_version.class_level else "Unknown"
        return f"{teacher_name} @ {self.workstation.school_name} ({class_level})"

    @property
    def class_level(self):
        return self.subject_version.class_level if self.subject_version else None