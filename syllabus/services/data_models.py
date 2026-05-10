# syllabus/services/data_models.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date, time, datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# ==========================================================
# PERIOD CALCULATION RESULT MODEL
# ==========================================================
@dataclass(frozen=True)
class PeriodCalculation:
    """
    Represents derived values used when distributing syllabus periods
    across the school calendar.
    """
    total_periods: int
    periods_per_week: int

    required_weeks: float
    available_weeks: int
    available_periods: int

    period_difference: float
    distribution_ratio: float
    adjusted_periods_per_week: float


# ==========================================================
# WEEKLY SCHEDULE ITEM (SCHEME OF WORK ROW) - UPDATED
# ==========================================================
@dataclass
class ScheduleItem:
    # Calendar positioning
    week_number: int  # Single week number (for backward compatibility)
    calendar_week: int  # ISO week number
    month: str  # Month name(s): "Januari" or "Januari,Februari" for merged
    
    # Competence hierarchy
    main_competence: str
    specific_competence: str

    # Learning activities
    learning_activity: str
    student_activity: str

    # Period assignment
    periods: int

    # Teaching process & resources
    methodology: str
    assessment_criteria: Optional[str]
    teaching_aids: Optional[str]
    references: Optional[str]
    
    # Defaults
    weeks_display: str = ""  # "3,4" or "1,2,3" for merged weeks
    week_date: Optional[date] = None
    remarks: Optional[str] = ""
    week_numbers: List[int] = field(default_factory=list)  # List ya week numbers zote

    def __post_init__(self):
        """Initialize weeks_display if not provided."""
        if not self.weeks_display:
            if self.week_numbers:
                self.weeks_display = ",".join(str(w) for w in sorted(self.week_numbers))
            elif self.week_number:
                self.weeks_display = str(self.week_number)


# ==========================================================
# SCHEME IDENTIFICATION
# ==========================================================
@dataclass
class SchemeIdentification:
    teacher_name: str
    school_name: str
    language: str  # "sw" au "en" kulingana na SubjectVersion


# ==========================================================
# SCHEME OF WORK DATA CONTAINER
# ==========================================================
@dataclass
class SchemeData:
    """
    Final container for Scheme of Work.
    Built by SchemeBuilder
    Consumed by PDF generator
    """

    # --------------------------------------------------
    # NON-DEFAULT FIELDS (LAZIMA ZIWE JUU)
    # --------------------------------------------------

    # Administrative info
    council: str
    ward: str
    school_name: str
    teacher_name: str

    # Academic identifiers
    subject_name: str
    class_level_name: str
    year: str
    term: str
    term_display: str

    # Calendar & periods
    calendar_data: dict
    period_calculation: PeriodCalculation

    # Identification (new)
    identification: SchemeIdentification
    
    # Scheme table rows
    schedule_items: List[ScheduleItem]

    # --------------------------------------------------
    # DEFAULT FIELDS (ZIKO CHINI)
    # --------------------------------------------------

    # Scheme meta
    objectives: List[str] = field(default_factory=list)
    headers: List[str] = field(default_factory=list)


# ==================================================
# STUDENT COUNTS
# ==================================================
@dataclass
class StudentCount:
    boys: int
    girls: int

    @property
    def total(self) -> int:
        return self.boys + self.girls


# ==================================================
# LESSON IDENTIFICATION
# ==================================================
@dataclass
class LessonIdentification:
    school_name: str
    teacher_name: str
    main_competence: str
    class_level: str

    period: int
    date: date

    time_start: time
    time_finish: time

    language: str = "sw"  # default Kiswahili

    # ----------------------------------
    # Computed properties
    # ----------------------------------
    @property
    def duration(self) -> str:
        """
        Returns lesson duration in minutes or HH:MM format.
        Example: '40 min' or '01:20'
        """
        if not self.time_start or not self.time_finish:
            return ""

        start_dt = datetime.combine(self.date, self.time_start)
        end_dt = datetime.combine(self.date, self.time_finish)

        if end_dt <= start_dt:
            return ""

        delta: timedelta = end_dt - start_dt
        minutes = int(delta.total_seconds() // 60)

        # Simple readable format
        return f"{minutes} min"


# ==================================================
# LESSON PLAN META (NEW - FOR BACKWARD COMPATIBILITY)
# ==================================================
@dataclass
class LessonPlanMeta:
    """Metadata for lesson plan (required for serializer compatibility)"""
    subject: str
    class_level: str
    teacher: str
    school: str
    date: date
    period: int
    timestart: time
    timefinish: time


# ==================================================
# SUBJECT INFORMATION
# ==================================================
@dataclass
class LessonSubjectInfo:
    specific_competence: str
    main_activity: str
    specific_activity: str
    teaching_aids: str
    references: str


# ==================================================
# LESSON STEP (TABLE ROW)
# ==================================================
@dataclass
class LessonStep:
    step_name: str                 # Utangulizi, Kuimarisha, n.k.
    duration: timedelta
    teaching_activity: str
    learning_activity: str
    assessment_indicator: str


# ==================================================
# REFLECTION / COMMENTS
# ==================================================
@dataclass
class LessonReflection:
    teaching_comment: Optional[str] = ""
    assessment_comment: Optional[str] = ""
    next_plan_comment: Optional[str] = ""


# ==================================================
# LESSON PLAN DATA (⭐ FINAL DTO - UPDATED WITH META)
# ==================================================
@dataclass
class LessonPlanData:
    # Identification
    identification: LessonIdentification

    # Attendance
    registered_students: StudentCount
    attended_students: StudentCount

    # Subject
    subject_info: LessonSubjectInfo

    # Teaching process
    lesson_steps: List[LessonStep] = field(default_factory=list)

    # Reflection
    reflection: Optional[LessonReflection] = None
    
    # 🔴 FIX: ADD META FIELD (REQUIRED FOR SERIALIZER)
    meta: Optional[LessonPlanMeta] = None
    
    # ----------------------------------
    # Computed properties
    # ----------------------------------
    @property
    def total_registered(self) -> int:
        return self.registered_students.total
    
    @property
    def total_attended(self) -> int:
        return self.attended_students.total
    
    @property
    def total_duration_minutes(self) -> int:
        """Calculate total duration of all lesson steps in minutes."""
        total = 0
        for step in self.lesson_steps:
            total += int(step.duration.total_seconds() // 60)
        return total


# ==================================================
# HELPER FUNCTION TO CREATE MERGED SCHEDULE ITEMS
# ==================================================
def create_merged_schedule_item(
    months: List[str],
    weeks: List[int],
    total_periods: int,
    main_competence: str = "",
    specific_competence: str = "",
    learning_activity: str = "",
    student_activity: str = "",
    methodology: str = "",
    assessment_criteria: Optional[str] = None,
    teaching_aids: Optional[str] = None,
    references: Optional[str] = None,
    week_date: Optional[date] = None,
    remarks: str = "",
    is_special: bool = False
) -> ScheduleItem:
    """
    Helper function to create a ScheduleItem with merged weeks.
    
    Args:
        months: List of month names ["Januari"] or ["Januari", "Februari"]
        weeks: List of week numbers [3, 4] or [1, 2, 3]
        total_periods: Total periods for the merged weeks
        is_special: True for holiday/exam rows
    """
    logger.debug(f"Creating merged schedule item: months={months}, weeks={weeks}, periods={total_periods}, special={is_special}")
    
    # Sort months by order
    month_order = {
        "Januari": 1, "Februari": 2, "Machi": 3, "Aprili": 4,
        "Mei": 5, "Juni": 6, "Julai": 7, "Agosti": 8,
        "Septemba": 9, "Oktoba": 10, "Novemba": 11, "Desemba": 12
    }
    months_sorted = sorted(months, key=lambda m: month_order.get(m, 13))
    
    # Format months display
    if len(months_sorted) == 1:
        months_display = months_sorted[0]
    else:
        months_display = ",".join(months_sorted)
    
    # Format weeks display
    weeks_sorted = sorted(weeks)
    weeks_display = ",".join(str(w) for w in weeks_sorted)
    
    # For special rows (holidays/exams), clear activity fields
    if is_special:
        main_competence = ""
        specific_competence = ""
        learning_activity = ""
        methodology = ""
        assessment_criteria = None
        teaching_aids = None
        references = None
    
    # Create the item
    item = ScheduleItem(
        week_number=weeks_sorted[0] if weeks_sorted else 0,  # First week for backward compatibility
        calendar_week=0,  # Not used for merged items
        month=months_display,
        weeks_display=weeks_display,
        week_numbers=weeks_sorted,  # Store all week numbers
        main_competence=main_competence,
        specific_competence=specific_competence,
        learning_activity=learning_activity,
        student_activity=student_activity,
        periods=total_periods if not is_special else 0,
        methodology=methodology,
        assessment_criteria=assessment_criteria,
        teaching_aids=teaching_aids,
        references=references,
        week_date=week_date,
        remarks=remarks
    )
    
    logger.debug(f"Created item: month={item.month}, weeks={item.weeks_display}, activity={item.student_activity[:30]}")
    return item