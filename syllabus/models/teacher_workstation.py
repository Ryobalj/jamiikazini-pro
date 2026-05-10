# syllabus/models/teacher_workstation.py

from django.db import models
from django.conf import settings
from kiini.models.base import UUIDModel, TimeStampedModel
from django.utils.translation import gettext_lazy as _


class TeacherWorkStation(UUIDModel, TimeStampedModel):
    """
    Taarifa za mwalimu kuhusu kituo chake cha kazi.
    Kila mwalimu anaweza kuwa na workstation moja tu.
    """

    teacher = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workstation",
        help_text=_("1. Chagua mwalimu anayehusiana na workstation hii. Mfano: 'ryoba.dennis@jamiikazini.com'")
    )
    school_name = models.CharField(
        max_length=255,
        help_text=_("2. Jina la shule ambapo mwalimu anafanya kazi. Mfano: 'Shule ya Msingi Mzingi'")
    )
    district = models.CharField(
        max_length=255,
        help_text=_("3. Jina la wilaya. Mfano: 'Halimashauri ya Wilaya ya Mkinga'")
    )
    ward = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("4. Jina la kata (hiari). Mfano: 'Kata ya Parungu Kasera'")
    )
    region = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("5. Jina la mkoa (hiari). Mfano: 'Tanga'")
    )

    is_active = models.BooleanField(
        default=True,
        help_text=_("6. Weka False ikiwa mwalimu hafanyi kazi tena hapa. Mfano: False")
    )

    class Meta:
        verbose_name = _("Sehemu ya Kazi ya Mwalimu")
        verbose_name_plural = _("Sehemu za Kazi za Walimu")

    def __str__(self):
        return f"{self.teacher.username} @ {self.school_name} ({self.district})"