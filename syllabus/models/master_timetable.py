# syllabus/models/master_timetable.py
#
# Whole-school master timetable generation - a self-contained subsystem
# separate from TimeTable (a teacher's own personal "Ratiba Yangu"). A
# teacher builds a roster of colleagues (no login required - they're
# lightweight name+initials entries, not real accounts) and what each
# teaches, and the system auto-generates a conflict-free day/period grid
# from muhtasari periods_per_week data. Scoped strictly to the creating
# teacher's own account - it never writes into anyone's personal TimeTable.

from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.timetable import TimeTable


class MasterTimetableRoster(UUIDModel, TimeStampedModel):
    """One school-year's worth of master-timetable data for a school,
    owned by the teacher who built it."""

    owner = models.ForeignKey(
        TeacherWorkStation,
        on_delete=models.CASCADE,
        related_name="master_timetable_rosters",
        verbose_name=_("Mmiliki"),
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Jina"),
        help_text=_("Mfano: Ratiba Kuu 2026"),
    )
    year = models.PositiveSmallIntegerField(verbose_name=_("Mwaka"))
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Ratiba Kuu - Roster")
        verbose_name_plural = _("Ratiba Kuu - Rosters")
        ordering = ["-year", "-created_at"]
        unique_together = ("owner", "year")

    def __str__(self):
        return f"{self.name} ({self.year}) - {self.owner.school_name}"


class TimetablePeriodSlot(UUIDModel):
    """A single position in the school day - either a real teaching
    period or a named break. Per-roster (not hardcoded) because real
    school days interleave numbered periods with named breaks in a way
    TimeTable.PERIODS (a flat 1-10 range) can't represent."""

    roster = models.ForeignKey(
        MasterTimetableRoster,
        on_delete=models.CASCADE,
        related_name="period_slots",
        verbose_name=_("Roster"),
    )
    order = models.PositiveSmallIntegerField(
        verbose_name=_("Mpangilio"),
        help_text=_("Nafasi ya kipindi hiki siku nzima, kwa mpangilio (1, 2, 3, ...)."),
    )
    label = models.CharField(
        max_length=20,
        verbose_name=_("Jina la Kipindi"),
        help_text=_("Mfano: '1', '2', au 'MAPUMZIKO' kwa mapumziko."),
    )
    timestart = models.TimeField(null=True, blank=True, verbose_name=_("Muda wa Kuanza"))
    timefinish = models.TimeField(null=True, blank=True, verbose_name=_("Muda wa Kumaliza"))
    is_break = models.BooleanField(
        default=False,
        verbose_name=_("Ni Mapumziko"),
        help_text=_("Vipindi vya mapumziko havijumuishwi kwenye kizazi cha ratiba."),
    )

    class Meta:
        verbose_name = _("Nafasi ya Kipindi")
        verbose_name_plural = _("Nafasi za Vipindi")
        ordering = ["roster", "order"]
        unique_together = ("roster", "order")

    def __str__(self):
        return f"{self.roster.name}: #{self.order} {self.label}"


class ActivityType(UUIDModel, TimeStampedModel):
    """Admin-managed reference list of non-subject period activities
    (arrival, cleaning, assembly, sports, clubs, religion, etc.) - a
    fixed built-in list with a free-text custom fallback on the slot
    itself for anything school-specific."""

    code = models.CharField(max_length=30, unique=True, verbose_name=_("Msimbo"))
    label_sw = models.CharField(max_length=100, verbose_name=_("Jina (Kiswahili)"))
    label_en = models.CharField(max_length=100, verbose_name=_("Jina (Kiingereza)"))
    is_fixed_routine = models.BooleanField(
        default=False,
        verbose_name=_("Ni Utaratibu wa Kila Siku"),
        help_text=_(
            "Mfano: kuwasili, usafi wa mazingira, mstarini na ukaguzi - hutokea "
            "kila siku bila kubadilika, hivyo huonyeshwa kama safu maalum kabla "
            "ya vipindi, si sehemu ya kizazi cha ratiba."
        ),
    )
    is_whole_school = models.BooleanField(
        default=False,
        verbose_name=_("Huathiri Shule Nzima"),
        help_text=_("Mfano: michezo, klabu, dini - hutumika kwa madarasa yote kwa wakati mmoja."),
    )
    default_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = _("Aina ya Shughuli")
        verbose_name_plural = _("Aina za Shughuli")
        ordering = ["default_order", "code"]

    def __str__(self):
        return self.label_sw


class TimetableTeacher(UUIDModel, TimeStampedModel):
    """A colleague teacher on the roster - a lightweight entry (name +
    initials) the roster owner types in directly, not a real account.
    workstation is an optional seam for a future "link once they sign
    up" fast-follow - unused in v1."""

    roster = models.ForeignKey(
        MasterTimetableRoster,
        on_delete=models.CASCADE,
        related_name="teachers",
        verbose_name=_("Roster"),
    )
    full_name = models.CharField(max_length=255, verbose_name=_("Jina Kamili"))
    initials = models.CharField(
        max_length=10,
        verbose_name=_("Herufi za Awali"),
        help_text=_("Herufi fupi zinazomtambulisha mwalimu kwenye ratiba, mfano 'DR'."),
    )
    workstation = models.ForeignKey(
        TeacherWorkStation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="master_timetable_entries",
        verbose_name=_("Kituo cha Kazi"),
        help_text=_("Ikiwa mwalimu huyu ana akaunti yake mwenyewe (hiari)."),
    )

    class Meta:
        verbose_name = _("Mwalimu (Roster)")
        verbose_name_plural = _("Walimu (Roster)")
        ordering = ["roster", "initials"]
        unique_together = ("roster", "initials")

    def __str__(self):
        return f"{self.full_name} ({self.initials})"


class TimetableTeacherAssignment(UUIDModel, TimeStampedModel):
    """A teacher-subject-class fact: this teacher teaches this
    subject_version. periods_per_week_override exists because
    Subject.periods_per_week is class-agnostic (same number regardless
    of which class studies it), but real schools vary it per class."""

    roster = models.ForeignKey(
        MasterTimetableRoster,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("Roster"),
    )
    teacher = models.ForeignKey(
        TimetableTeacher,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("Mwalimu"),
    )
    subject_version = models.ForeignKey(
        "syllabus.SubjectVersion",
        on_delete=models.PROTECT,
        related_name="master_timetable_assignments",
        verbose_name=_("Somo (Darasa)"),
    )
    periods_per_week_override = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Vipindi kwa Wiki (Badiliko)"),
        help_text=_(
            "Ikiachwa wazi, idadi ya vipindi kwa wiki itatumika kutoka kwenye "
            "muhtasari (Somo.periods_per_week)."
        ),
    )

    class Meta:
        verbose_name = _("Ugawaji wa Mwalimu")
        verbose_name_plural = _("Ugawaji wa Walimu")
        ordering = ["roster", "teacher"]
        unique_together = ("teacher", "subject_version")

    def __str__(self):
        return f"{self.teacher.initials} - {self.subject_version}"

    @property
    def effective_periods_per_week(self) -> int:
        return self.periods_per_week_override or self.subject_version.subject.periods_per_week


class TimetableSlot(UUIDModel, TimeStampedModel):
    """One cell in the generated/manually-placed master timetable grid.
    class_level=None means a whole-school activity (e.g. Friday DINI
    applying to every class at once) - one row, not one per class,
    matching the source Excel's merged-cell-across-all-classes rows.

    No DB unique_together here: class_level is nullable, and a nullable-
    column uniqueness constraint is exactly what forced TimeTable to drop
    its own constraint (NULL != NULL lets duplicates through silently).
    Uniqueness is guaranteed by construction (the generator and manual-
    placement flow only ever create one row per day/period/class) plus a
    serializer validate() check, the same pattern TimeTableSerializer
    already uses for its own clash check.
    """

    class Source(models.TextChoices):
        GENERATED = "GENERATED", _("Kiotomatiki")
        MANUAL = "MANUAL", _("Kwa Mkono")

    roster = models.ForeignKey(
        MasterTimetableRoster,
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name=_("Roster"),
    )
    day_of_week = models.IntegerField(
        choices=TimeTable.DayOfWeek.choices,
        verbose_name=_("Siku ya Wiki"),
    )
    period_slot = models.ForeignKey(
        TimetablePeriodSlot,
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name=_("Nafasi ya Kipindi"),
    )
    class_level = models.ForeignKey(
        "syllabus.ClassLevel",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="master_timetable_slots",
        verbose_name=_("Darasa"),
        help_text=_("Ikiachwa wazi, shughuli hii inahusu shule nzima (madarasa yote kwa wakati mmoja)."),
    )
    assignment = models.ForeignKey(
        TimetableTeacherAssignment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="slots",
        verbose_name=_("Ugawaji"),
    )
    activity_type = models.ForeignKey(
        ActivityType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="slots",
        verbose_name=_("Aina ya Shughuli"),
    )
    custom_label = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Jina Maalum"),
        help_text=_("Tumia hii kwa shughuli isiyo kwenye orodha ya kawaida."),
    )
    source = models.CharField(
        max_length=10,
        choices=Source.choices,
        default=Source.GENERATED,
        verbose_name=_("Chanzo"),
    )

    class Meta:
        verbose_name = _("Kiini cha Ratiba Kuu")
        verbose_name_plural = _("Viini vya Ratiba Kuu")
        ordering = ["roster", "day_of_week", "period_slot__order", "class_level"]

    def __str__(self):
        target = self.class_level.name if self.class_level else "Shule Nzima"
        what = (
            self.assignment.subject_version.subject.name if self.assignment
            else (self.activity_type.label_sw if self.activity_type else self.custom_label)
        )
        return f"{self.get_day_of_week_display()} #{self.period_slot.order} {target}: {what}"
