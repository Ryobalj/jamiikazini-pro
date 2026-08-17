# syllabus/services/calendar_service.py

from datetime import date, timedelta
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any, Tuple
from django.utils.translation import gettext_lazy as _
import logging

from syllabus.models.annual_calendar import AnnualCalendar

logger = logging.getLogger(__name__)


# =====================================================
# DATA STRUCTURE
# =====================================================

@dataclass(frozen=True)
class CalendarBlock:
    """
    Represents a continuous calendar block.
    """
    block_type: str  # 'study' | 'break'
    start_date: date
    end_date: date
    week_numbers: List[int]
    block_name: str = ""  # Field mpya kwa ajili ya aina ya block

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    @property
    def learning_days(self) -> int:
        """
        Count learning days (Mon–Fri) for study blocks only.
        """
        if self.block_type != "study":
            return 0

        count = 0
        current = self.start_date
        while current <= self.end_date:
            if current.weekday() < 5:
                count += 1
            current += timedelta(days=1)
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'block_type': self.block_type,
            'block_name': self.block_name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'week_numbers': self.week_numbers,
            'duration_days': self.duration_days,
            'learning_days': self.learning_days,
        }


# =====================================================
# SERVICE
# =====================================================

class CalendarService:
    """
    Core academic calendar service.

    Responsibilities:
    - Validate academic calendar integrity
    - Split calendar into study / break blocks
    - Calculate studying weeks and learning days
    """

    def __init__(self, calendar: AnnualCalendar):
        if not calendar:
            raise ValueError(_("AnnualCalendar instance is required"))

        self.calendar = calendar
        self.year = calendar.year

        self._blocks: Optional[List[CalendarBlock]] = None
        self._studying_weeks: Optional[List[int]] = None
        self._break_weeks: Optional[List[int]] = None
        self._learning_days: Optional[int] = None

        self._validate_calendar()

    # ==================================================
    # VALIDATION
    # ==================================================

    def _validate_calendar(self) -> None:
        """
        Ensures calendar is complete, ordered and logically consistent.
        """
        logger.info(f"Validating calendar for year {self.year}")

        required_fields = [
            "term_start_date",
            "midterm_break_start_date",
            "midterm_start_date",
            "term_break_start_date",
            "annual_startdate",
            "midannual_break_start_date",
            "midannual_start_date",
            "annual_break_start_date",
        ]

        missing = [
            field for field in required_fields
            if not getattr(self.calendar, field, None)
        ]

        if missing:
            error_msg = _("Calendar missing required dates: {}").format(", ".join(missing))
            logger.error(f"Calendar validation failed: {error_msg}")
            raise ValueError(error_msg)

        ordered_dates = [
            self.calendar.term_start_date,
            self.calendar.midterm_break_start_date,
            self.calendar.midterm_start_date,
            self.calendar.term_break_start_date,
            self.calendar.annual_startdate,
            self.calendar.midannual_break_start_date,
            self.calendar.midannual_start_date,
            self.calendar.annual_break_start_date,
        ]

        for i in range(len(ordered_dates) - 1):
            if ordered_dates[i] > ordered_dates[i + 1]:
                error_msg = _(
                    "Calendar dates are not in chronological order "
                    "({} comes after {})."
                ).format(ordered_dates[i], ordered_dates[i + 1])
                logger.error(f"Calendar validation failed: {error_msg}")
                raise ValueError(error_msg)

        # Academic year span validation
        for d in ordered_dates:
            if d.year not in (self.year, self.year + 1):
                error_msg = _("Calendar date {} is outside expected academic year").format(d)
                logger.warning(f"Calendar date validation warning: {error_msg}")
                # Don't raise error, just warn for flexibility

        logger.info(f"Calendar validation passed for year {self.year}")

    # ==================================================
    # BLOCK GENERATION
    # ==================================================

    def get_blocks(self, refresh: bool = False) -> List[CalendarBlock]:
        """Get all calendar blocks (cached)."""
        if self._blocks is None or refresh:
            self._blocks = self._build_blocks()
        return self._blocks

    def _build_blocks(self) -> List[CalendarBlock]:
        """Build calendar blocks from AnnualCalendar dates."""
        logger.debug(f"Building calendar blocks for year {self.year}")
        blocks: List[CalendarBlock] = []

        # Define blocks with proper names
        periods = [
            ("term_start_date", "midterm_break_start_date", "study", "Term I - Study"),
            ("midterm_break_start_date", "midterm_start_date", "break", "Midterm Break"),
            ("midterm_start_date", "term_break_start_date", "study", "Term I - Study (Post Midterm)"),
            ("term_break_start_date", "annual_startdate", "break", "Term Break"),
            ("annual_startdate", "midannual_break_start_date", "study", "Term II - Study"),
            ("midannual_break_start_date", "midannual_start_date", "break", "Midannual Break"),
            ("midannual_start_date", "annual_break_start_date", "study", "Term II - Study (Post Midannual)"),
            ("annual_break_start_date", None, "break", "Annual Break"),
        ]

        for start_field, end_field, block_type, block_name in periods:
            start_date: date = getattr(self.calendar, start_field)

            if end_field:
                end_date: date = getattr(self.calendar, end_field)
            else:
                # Final break (Annual Break) has no explicit end date in the
                # model. Schools reopen a few days into January, not on
                # 31 Dec — so prefer the following year's real term start
                # date (if that calendar has been seeded yet) and fall back
                # to the same early-January convention used when seeding
                # (e.g. 6 Jan) otherwise.
                next_year_calendar = (
                    AnnualCalendar.objects
                    .filter(institute=self.calendar.institute, year=self.year + 1)
                    .first()
                )
                if next_year_calendar and next_year_calendar.term_start_date:
                    end_date = next_year_calendar.term_start_date - timedelta(days=1)
                else:
                    end_date = date(self.year + 1, 1, 6)

            if start_date > end_date:
                logger.warning(
                    "Skipped invalid block (%s): %s > %s",
                    block_type, start_date, end_date
                )
                continue

            blocks.append(
                CalendarBlock(
                    block_type=block_type,
                    start_date=start_date,
                    end_date=end_date,
                    week_numbers=self._get_week_numbers(start_date, end_date),
                    block_name=block_name
                )
            )

        logger.info(f"Built {len(blocks)} calendar blocks for year {self.year}")
        return blocks

    def _get_week_numbers(self, start: date, end: date) -> List[int]:
        """Get ISO week numbers between start and end dates."""
        weeks = set()
        current = start
        while current <= end:
            weeks.add(current.isocalendar()[1])
            current += timedelta(days=1)
        return sorted(weeks)

    # ==================================================
    # DERIVED CALCULATIONS
    # ==================================================

    def get_studying_weeks(self, refresh: bool = False) -> List[int]:
        """Get all studying week numbers."""
        if self._studying_weeks is None or refresh:
            weeks = []
            for block in self.get_blocks(refresh):
                if block.block_type == "study":
                    weeks.extend(block.week_numbers)
            self._studying_weeks = sorted(set(weeks))
        return self._studying_weeks

    def get_break_weeks(self, refresh: bool = False) -> List[int]:
        """Get all break week numbers."""
        if self._break_weeks is None or refresh:
            weeks = []
            for block in self.get_blocks(refresh):
                if block.block_type == "break":
                    weeks.extend(block.week_numbers)
            self._break_weeks = sorted(set(weeks))
        return self._break_weeks

    def total_learning_days(self, refresh: bool = False) -> int:
        """Calculate total learning days (Mon-Fri in study blocks)."""
        if self._learning_days is None or refresh:
            self._learning_days = sum(
                block.learning_days for block in self.get_blocks(refresh)
            )
        return self._learning_days

    # ==================================================
    # NEW METHODS FOR SCHEME TIMELINE BUILDER
    # ==================================================

    def get_study_blocks(self) -> List[CalendarBlock]:
        """Get only study blocks."""
        return [block for block in self.get_blocks() if block.block_type == "study"]

    def get_break_blocks(self) -> List[CalendarBlock]:
        """Get only break blocks."""
        return [block for block in self.get_blocks() if block.block_type == "break"]

    def get_break_blocks_with_names(self) -> List[Dict[str, Any]]:
        """Get break blocks with their names for holiday identification."""
        break_blocks = self.get_break_blocks()
        
        # Create new dictionaries with holiday types
        blocks_with_names = []
        for block in break_blocks:
            block_dict = block.to_dict()
            
            # Determine holiday type
            if "midterm" in block_dict['block_name'].lower():
                holiday_type = "midterm"
            elif "midannual" in block_dict['block_name'].lower():
                holiday_type = "midannual"
            elif "annual" in block_dict['block_name'].lower():
                holiday_type = "annual"
            elif "term" in block_dict['block_name'].lower() and "break" in block_dict['block_name'].lower():
                holiday_type = "terminal"
            else:
                # Fallback based on month
                month = block.start_date.month
                if month in [4, 5]:
                    holiday_type = "midterm"
                elif month in [8]:
                    holiday_type = "midannual"
                elif month in [12, 1]:
                    holiday_type = "annual"
                else:
                    holiday_type = "terminal"
            
            # Add holiday info to dictionary
            block_dict['holiday_type'] = holiday_type
            block_dict['holiday_label'] = self._get_holiday_label(holiday_type)
            block_dict['exam_label'] = self._get_exam_label(holiday_type)
            
            blocks_with_names.append(block_dict)
        
        return blocks_with_names

    def get_week_block_type(self, week_number: int) -> Optional[str]:
        """Get block type for a specific week number."""
        for block in self.get_blocks():
            if week_number in block.week_numbers:
                return block.block_type
        return None

    def is_studying_week(self, week_number: int) -> bool:
        """Check if a week is a studying week."""
        return week_number in self.get_studying_weeks()

    def is_break_week(self, week_number: int) -> bool:
        """Check if a week is a break week."""
        return week_number in self.get_break_weeks()

    # Exam weeks immediately before each break type, per real Tanzanian
    # school calendar convention: Robo Muhula (midterm/midannual) breaks
    # each have 1 week of exams; the end-of-Term-I break and the annual
    # break are both full end-of-term/end-of-year examination periods,
    # each with 2 weeks of exams.
    _EXAM_WEEKS_BY_HOLIDAY_TYPE = {
        "midterm": 1,
        "midannual": 1,
        "terminal": 2,
        "annual": 2,
    }

    def get_exam_weeks_before_break(self) -> Dict[str, List[int]]:
        """Get exam weeks that come before break blocks."""
        exam_weeks = {}

        for block in self.get_break_blocks():
            if block.block_type == "break" and block.week_numbers:
                # Use the ISO week of the block's actual start date rather
                # than min(week_numbers): the Annual Break now runs into
                # January of the next year (schools reopen a few days after
                # New Year, not on 31 Dec), so week_numbers mixes late-year
                # week numbers (e.g. 49-52) with early-year ones (1-2) from
                # the January tail — min() would wrongly pick the January
                # week as the block's "first" week.
                first_break_week = block.start_date.isocalendar()[1]

                # _determine_holiday_type() checks "midterm"/"midannual"
                # before the generic "annual" substring, unlike a naive
                # `"annual" in block_name` check here (which would wrongly
                # match "Midannual Break" too, since "annual" is a
                # substring of "midannual").
                holiday_type = self._determine_holiday_type(block)
                count = self._EXAM_WEEKS_BY_HOLIDAY_TYPE.get(holiday_type, 1)

                weeks = [
                    week for week in range(first_break_week - count, first_break_week)
                    if week > 0
                ]
                if weeks:
                    exam_weeks[block.block_name] = weeks

        logger.debug(f"Found exam weeks before breaks: {exam_weeks}")
        return exam_weeks

    def get_pre_break_exclusion_ranges(self) -> List[Tuple[date, date]]:
        """Real date ranges (inclusive) that must not receive new teaching
        content: from the start of the exam period through the day before
        the break actually begins.

        Real schools stop new instruction once exams start for a block and
        don't resume before the holiday — but ISO week numbers alone can't
        reliably capture this at a block boundary: when a break doesn't
        start on a Monday, the days between the end of the (single) ISO
        exam week and the break's real start_date still belong to the
        study block's own week_numbers, so week-number matching alone
        leaves a few real days (and sometimes a whole extra week) where
        new content would otherwise still get scheduled between the exam
        and the holiday.
        """
        ranges: List[Tuple[date, date]] = []
        for block in self.get_break_blocks():
            # Same holiday_type -> exam-week-count mapping used by
            # get_exam_weeks_before_break() (a naive `"annual" in
            # block_name` check here would wrongly match "Midannual Break"
            # too, since "annual" is a substring of "midannual").
            holiday_type = self._determine_holiday_type(block)
            exam_weeks_count = self._EXAM_WEEKS_BY_HOLIDAY_TYPE.get(holiday_type, 1)
            exam_days = exam_weeks_count * 7
            start = block.start_date - timedelta(days=exam_days)
            end = block.start_date - timedelta(days=1)
            if start <= end:
                ranges.append((start, end))
        return ranges

    def get_holiday_info_for_week(self, week_number: int) -> Dict[str, Any]:
        """Get holiday information for a specific week."""
        for block in self.get_blocks():
            if week_number in block.week_numbers:
                holiday_type = self._determine_holiday_type(block)
                return {
                    "block_type": block.block_type,
                    "block_name": block.block_name,
                    "start_date": block.start_date,
                    "end_date": block.end_date,
                    "week_numbers": block.week_numbers,
                    "is_holiday": block.block_type == "break",
                    "holiday_type": holiday_type,
                    "holiday_label": self._get_holiday_label(holiday_type),
                    "exam_label": self._get_exam_label(holiday_type)
                }
        return {"is_holiday": False}

    def _determine_holiday_type(self, block: CalendarBlock) -> str:
        """Determine holiday type based on block dates and name."""
        block_name = block.block_name.lower()
        
        if "midterm" in block_name:
            return "midterm"
        elif "midannual" in block_name:
            return "midannual"
        elif "annual" in block_name:
            return "annual"
        elif "term" in block_name and "break" in block_name:
            return "terminal"
        else:
            # Fallback based on month
            month = block.start_date.month
            if month in [4, 5]:  # April/May
                return "midterm"
            elif month in [8]:  # August
                return "midannual"
            elif month in [12, 1]:  # December/January
                return "annual"
            else:
                return "terminal"

    def _get_holiday_label(self, holiday_type: str) -> str:
        """Get holiday label based on type. "midterm"/"midannual" are the
        structurally equivalent mid-term breaks of Muhula I and Muhula II
        respectively, labelled "I"/"II" for consistency (matches the
        "Muhula wa I & II" convention) instead of unrelated terms."""
        labels = {
            "midterm": "LIKIZO YA ROBO MUHULA I",
            "midannual": "LIKIZO YA ROBO MUHULA II",
            "annual": "LIKIZO YA MWISHO WA MWAKA",
            "terminal": "LIKIZO YA MWISHO WA MUHULA"
        }
        return labels.get(holiday_type, "LIKIZO")

    def _get_exam_label(self, holiday_type: str) -> str:
        """Get exam label based on holiday type."""
        labels = {
            "midterm": "MITIHANI YA ROBO MUHULA I",
            "midannual": "MITIHANI YA ROBO MUHULA II",
            "annual": "MITIHANI YA MWISHO WA MWAKA",
            "terminal": "MITIHANI YA MWISHO WA MUHULA"
        }
        return labels.get(holiday_type, "MTIHANI")

    # ==================================================
    # SUMMARY AND SERIALIZATION
    # ==================================================

    def get_calendar_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the calendar."""
        blocks = self.get_blocks()
        studying_weeks = self.get_studying_weeks()
        break_weeks = self.get_break_weeks()
        
        return {
            'year': self.year,
            'institute': getattr(self.calendar, 'institute', 'Unknown'),
            'total_blocks': len(blocks),
            'study_blocks': len(self.get_study_blocks()),
            'break_blocks': len(self.get_break_blocks()),
            'total_studying_weeks': len(studying_weeks),
            'total_break_weeks': len(break_weeks),
            'total_learning_days': self.total_learning_days(),
            'calendar_range': {
                'start': min(b.start_date for b in blocks).isoformat() if blocks else None,
                'end': max(b.end_date for b in blocks).isoformat() if blocks else None,
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert calendar service to serializable dictionary."""
        return {
            'summary': self.get_calendar_summary(),
            'blocks': [block.to_dict() for block in self.get_blocks()],
            'studying_weeks': self.get_studying_weeks(),
            'break_weeks': self.get_break_weeks(),
            'break_blocks_with_names': self.get_break_blocks_with_names()
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"CalendarService(year={self.year}, blocks={len(self.get_blocks())})"