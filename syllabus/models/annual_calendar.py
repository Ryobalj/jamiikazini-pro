# syllabus/models/annual_calendar.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel
from django.utils.translation import gettext_lazy as _
from datetime import date

class AnnualCalendar(UUIDModel, TimeStampedModel):
    """
    Kalenda ya mwaka wa masomo kwa taasisi: ina term start, midterm, midannual, breaks, evaluation, etc.
    Mwaka unaoonekana kwenye dropdown ni miaka mitatu tu: mwaka uliopita, huu, na ujao.

    Kidato cha Tano na Sita (A-Level) hawatumii kalenda ile ile ya Awali - Kidato
    cha Nne (Kindergarten/basic education/O-Level): Wizara ya Elimu hutoa Waraka
    wa Elimu tofauti kwa Kidato V-VI kila mwaka (mfano: Waraka wa Elimu Na. 1
    wa Mwaka 2026, unaoanza Muhula I mwezi Julai badala ya Januari). `level_group`
    hutofautisha kalenda hizi mbili ili ile sahihi itumike kiotomatiki kutegemea
    darasa husika, badala ya kalenda moja kutumika kwa madarasa yote.
    """

    MONTHS = (
        ('January', _('January')),
        ('February', _('February')),
        ('March', _('March')),
        ('April', _('April')),
        ('May', _('May')),
        ('June', _('June')),
        ('July', _('July')),
        ('August', _('August')),
        ('September', _('September')),
        ('October', _('October')),
        ('November', _('November')),
        ('December', _('December')),
    )

    WEEKS = ((1, _('Week 1')), (2, _('Week 2')), (3, _('Week 3')), (4, _('Week 4')))

    # 'basic' = Awali through Kidato IV (O-Level) - the calendar historically
    # seeded here and used for everyone until now.
    # 'advanced' = Kidato V-VI (A-Level) - follows the Ministry's separate
    # Kalenda ya Mihula kwa Kidato cha Tano na Sita (its academic year starts
    # mid-year, e.g. July, not January).
    LEVEL_GROUP_BASIC = 'basic'
    LEVEL_GROUP_ADVANCED = 'advanced'

    LEVEL_GROUP_CHOICES = (
        (LEVEL_GROUP_BASIC, _('Awali - Kidato IV (Msingi/O-Level)')),
        (LEVEL_GROUP_ADVANCED, _('Kidato V - VI (A-Level)')),
    )

    # ClassLevel.name values (see syllabus/csv/class_level.csv) that fall
    # under the 'advanced' calendar. Everything else in ClassLevel is 'basic'.
    ADVANCED_CLASS_LEVEL_NAMES = {"Kidato V", "Kidato VI"}

    def year_choices():
        current_year = date.today().year
        return [(y, str(y)) for y in range(current_year - 1, current_year + 2)]

    institute = models.CharField(
        max_length=255,
        verbose_name=_("Taasis ya Shule/Chuo"),
        help_text=_("Jina la shule au chuo. Mfano: 'Shule ya Msingi Mzingi'")
    )

    year = models.IntegerField(
        choices=year_choices(),
        default=date.today().year,
        verbose_name=_("Mwaka wa Masomo"),
        help_text=_("Chagua mwaka wa masomo (miaka mitatu tu: uliopita, huu, ujao).")
    )

    level_group = models.CharField(
        max_length=20,
        choices=LEVEL_GROUP_CHOICES,
        default=LEVEL_GROUP_BASIC,
        verbose_name=_("Kundi la Elimu"),
        help_text=_(
            "Kundi la madarasa yanayotumia kalenda hii: Awali-Kidato IV (basic) "
            "au Kidato V-VI (advanced)."
        ),
    )

    total_learning_days = models.PositiveIntegerField(
        verbose_name=_("Jumla ya Siku za Mafunzo"),
        help_text=_("Jumla ya siku za masomo kwa mwaka mzima.")
    )

    # Term 1 Start
    term_start_month = models.CharField(max_length=20, choices=MONTHS, default='January')
    term_start_week = models.IntegerField(choices=WEEKS, default=1)
    term_start_date = models.DateField(default=date.today)
    
    # Midterm Break Start
    midterm_break_start_month = models.CharField(max_length=20, choices=MONTHS, default='February')
    midterm_break_start_week = models.IntegerField(choices=WEEKS, default=1)
    midterm_break_start_date = models.DateField(default=date.today)
    
    # Midterm Start
    midterm_start_month = models.CharField(max_length=20, choices=MONTHS, default='February')
    midterm_start_week = models.IntegerField(choices=WEEKS, default=2)
    midterm_start_date = models.DateField(default=date.today)
    
    # Term Break Start
    term_break_start_month = models.CharField(max_length=20, choices=MONTHS, default='March')
    term_break_start_week = models.IntegerField(choices=WEEKS, default=1)
    term_break_start_date = models.DateField(default=date.today)

    # Annual start
    annual_startmonth = models.CharField(max_length=20,choices=MONTHS, default='January')
    annual_startweek = models.IntegerField(choices=WEEKS, default=1)
    annual_startdate = models.DateField(default=date.today)

    # Midannual Break Start
    midannual_break_start_month = models.CharField(max_length=20, choices=MONTHS, default='August')
    midannual_break_start_week = models.IntegerField(choices=WEEKS, default=1)
    midannual_break_start_date = models.DateField(default=date.today)

    # Midannual Start
    midannual_start_month = models.CharField(max_length=20, choices=MONTHS, default='July')
    midannual_start_week = models.IntegerField(choices=WEEKS, default=1)
    midannual_start_date = models.DateField(default=date.today)
    
    # Annual Break Start
    annual_break_start_month = models.CharField(max_length=20, choices=MONTHS, default='December')
    annual_break_start_week = models.IntegerField(choices=WEEKS, default=1)
    annual_break_start_date = models.DateField(default=date.today)

    status = models.BooleanField(default=True, verbose_name=_("Active"))

    class Meta:
        verbose_name = _("Kalenda ya Mwaka")
        verbose_name_plural = _("Kalenda za Mwaka")
        ordering = ["year", "institute", "level_group"]
        unique_together = ("year", "institute", "level_group")

    def __str__(self):
        return f"{self.institute} ({self.year}, {self.get_level_group_display()})"

    @classmethod
    def level_group_for_class_level(cls, class_level_name: str) -> str:
        """
        Given a ClassLevel.name (e.g. 'Kidato V', 'DRS III', 'Awali'),
        return which calendar level_group applies: 'advanced' for
        Kidato V/VI, 'basic' for everything else.
        """
        if (class_level_name or "").strip() in cls.ADVANCED_CLASS_LEVEL_NAMES:
            return cls.LEVEL_GROUP_ADVANCED
        return cls.LEVEL_GROUP_BASIC
