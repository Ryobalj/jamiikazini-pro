# syllabus/models/annual_calendar.py

from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel
from django.utils.translation import gettext_lazy as _
from datetime import date

class AnnualCalendar(UUIDModel, TimeStampedModel):
    """
    Kalenda ya mwaka wa masomo kwa taasisi: ina term start, midterm, midannual, breaks, evaluation, etc.
    Mwaka unaoonekana kwenye dropdown ni miaka mitatu tu: mwaka uliopita, huu, na ujao.
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
        ordering = ["year", "institute"]
        unique_together = ("year", "institute")

    def __str__(self):
        return f"{self.institute} ({self.year})"