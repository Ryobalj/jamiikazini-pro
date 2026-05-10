# syllabus/services/academic_context.py

from typing import Optional
from datetime import date, time
from django.core.exceptions import ValidationError


class AcademicContext:
    """
    Context container for academic information used in lesson planning.
    Provides validated access to teacher, school, timetable, and language data.
    """
    
    def __init__(
        self,
        *,
        workstation,
        timetable,
        subject_version,
        date: date,
        period: Optional[int] = None,
        timestart: Optional[time] = None,
        timefinish: Optional[time] = None,
        boys_attended: Optional[int] = None,
        girls_attended: Optional[int] = None,
        language: Optional[str] = None,
    ):
        """
        Initialize AcademicContext with validation.
        
        Args:
            workstation: TeacherWorkStation instance
            timetable: TimeTable instance
            subject_version: SubjectVersion instance
            date: Lesson date
            period: Optional lesson period (overrides timetable)
            timestart: Optional start time (overrides timetable)
            timefinish: Optional finish time (overrides timetable)
            boys_attended: Optional boys attendance count
            girls_attended: Optional girls attendance count
            language: Optional output language ('sw' or 'en')
        """
        
        # Validate required objects
        if not workstation:
            raise ValueError("Workstation is required")
        if not timetable:
            raise ValueError("Timetable is required")
        if not subject_version:
            raise ValueError("Subject version is required")
        if not date:
            raise ValueError("Date is required")
        
        self.workstation = workstation
        self.timetable = timetable
        self.subject_version = subject_version
        self.date = date

        # --------------------
        # CURRICULUM LANGUAGE
        # --------------------
        self.curriculum_language = "en" if subject_version.is_english else "sw"
        self.is_awali = subject_version.is_awali

        # --------------------
        # RUNTIME LANGUAGE
        # --------------------
        if language and language not in ["sw", "en"]:
            raise ValueError("Language must be 'sw' or 'en'")
        self.language = language or self.curriculum_language

        # --------------------
        # TIME & PERIOD WITH VALIDATION
        # --------------------
        self.period = self._validate_period(period)
        self.timestart = self._validate_time(timestart, "timestart")
        self.timefinish = self._validate_time(timefinish, "timefinish")
        
        # Validate time order
        if self.timestart and self.timefinish and self.timestart >= self.timefinish:
            raise ValueError("timestart must be earlier than timefinish")

        # --------------------
        # ATTENDANCE WITH VALIDATION
        # --------------------
        self.registered_boys = timetable.registeredboys or 0
        self.registered_girls = timetable.registeredgirls or 0
        
        self.boys_attended = self._validate_attendance(boys_attended, "boys_attended")
        self.girls_attended = self._validate_attendance(girls_attended, "girls_attended")

    # --------------------
    # VALIDATION HELPERS
    # --------------------
    def _validate_period(self, period: Optional[int]) -> int:
        """Validate and return period number."""
        if period is not None:
            if not isinstance(period, int) or period < 1:
                raise ValueError("Period must be a positive integer")
            return period
        
        # Fallback to timetable period
        if not self.timetable.period:
            return 1  # Default period
        return self.timetable.period

    def _validate_time(self, time_value: Optional[time], field_name: str) -> Optional[time]:
        """Validate time value."""
        if time_value is None:
            # Get from timetable
            if field_name == "timestart":
                return self.timetable.timestart
            else:  # timefinish
                return self.timetable.timefinish
        
        if not isinstance(time_value, time):
            raise ValueError(f"{field_name} must be a time object")
        return time_value

    def _validate_attendance(self, attendance: Optional[int], field_name: str) -> Optional[int]:
        """Validate attendance count."""
        if attendance is None:
            return None
        
        if not isinstance(attendance, int) or attendance < 0:
            raise ValueError(f"{field_name} must be a non-negative integer")
        
        # Check if attendance exceeds registered
        max_allowed = self.registered_boys if "boys" in field_name else self.registered_girls
        if attendance > max_allowed:
            # Log warning but allow (sometimes attendance > registered)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"{field_name} ({attendance}) exceeds registered count ({max_allowed})"
            )
        
        return attendance

    # --------------------
    # DERIVED PROPERTIES
    # --------------------
    @property
    def total_registered(self) -> int:
        """Total registered students."""
        return self.registered_boys + self.registered_girls

    @property
    def total_attended(self) -> Optional[int]:
        """Total attended students (returns None if attendance not recorded)."""
        if self.boys_attended is None and self.girls_attended is None:
            return None
        return (self.boys_attended or 0) + (self.girls_attended or 0)

    @property
    def attendance_percentage(self) -> Optional[float]:
        """Attendance percentage (0-100)."""
        if self.total_attended is None or self.total_registered == 0:
            return None
        return (self.total_attended / self.total_registered) * 100

    @property
    def duration_minutes(self) -> int:
        """Lesson duration in minutes."""
        if not self.timestart or not self.timefinish:
            return 0
        
        start_minutes = self.timestart.hour * 60 + self.timestart.minute
        end_minutes = self.timefinish.hour * 60 + self.timefinish.minute
        
        duration = end_minutes - start_minutes
        return max(duration, 0)  # Ensure non-negative

    @property
    def duration_formatted(self) -> str:
        """Formatted duration (e.g., '40 min' or '1:30')."""
        minutes = self.duration_minutes
        if minutes >= 60:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}:{mins:02d}"
        return f"{minutes} min"

    @property
    def school_name(self) -> str:
        """School name from workstation."""
        return self.workstation.school_name or ""

    @property
    def teacher_name(self) -> str:
        """Teacher's full name."""
        teacher = self.workstation.teacher
        if not teacher:
            return ""
        
        full_name = teacher.get_full_name()
        if full_name:
            return full_name
        return teacher.username or ""

    @property
    def class_level(self) -> str:
        """Class level name."""
        return self.subject_version.class_level.name or ""

    @property
    def subject_name(self) -> str:
        """Subject name."""
        return self.subject_version.subject.name or ""

    @property
    def is_english_medium(self) -> bool:
        """Whether subject is taught in English."""
        return self.curriculum_language == "en"

    @property
    def academic_year(self) -> str:
        """Academic year from subject version."""
        if hasattr(self.subject_version.syllabus_version, 'year'):
            return str(self.subject_version.syllabus_version.year)
        return ""

    # --------------------
    # UTILITY METHODS
    # --------------------
    def to_dict(self) -> dict:
        """Convert context to dictionary for serialization."""
        return {
            "school_name": self.school_name,
            "teacher_name": self.teacher_name,
            "class_level": self.class_level,
            "subject_name": self.subject_name,
            "date": self.date.isoformat() if self.date else None,
            "period": self.period,
            "timestart": self.timestart.isoformat() if self.timestart else None,
            "timefinish": self.timefinish.isoformat() if self.timefinish else None,
            "duration_minutes": self.duration_minutes,
            "language": self.language,
            "is_english_medium": self.is_english_medium,
            "is_awali": self.is_awali,
            "registered_students": {
                "boys": self.registered_boys,
                "girls": self.registered_girls,
                "total": self.total_registered,
            },
            "attended_students": {
                "boys": self.boys_attended,
                "girls": self.girls_attended,
                "total": self.total_attended,
                "percentage": self.attendance_percentage,
            },
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"AcademicContext("
            f"school={self.school_name}, "
            f"teacher={self.teacher_name}, "
            f"class={self.class_level}, "
            f"date={self.date}, "
            f"period={self.period})"
        )

    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.teacher_name} - {self.school_name} - {self.class_level} - Period {self.period}"