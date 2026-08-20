# syllabus/services/scheme_timeline_builder.py (VERSION MPYA KWA ALGORITHM SAHIHI)

from copy import deepcopy
from typing import List, Dict, Any, Tuple, Optional
from datetime import date, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict
import math

from syllabus.services.data_models import (
    SchemeData,
    SchemeIdentification,
    ScheduleItem,
    PeriodCalculation,
    create_merged_schedule_item
)
from syllabus.services.calendar_service import CalendarService
from syllabus.i18n import sw as sw_i18n, en as en_i18n

logger = logging.getLogger(__name__)


# ======================================================
# DATA STRUCTURES
# ======================================================
@dataclass
class Activity:
    """Represents a learning activity from syllabus."""
    index: int
    main_competence: str
    main_order: int
    specific_competence: str
    specific_order: int
    learning_activity: str
    learning_order: int
    specific_learning: str
    specific_learning_order: int
    periods_needed: int
    method: str
    assessment_criteria: str
    teaching_aids: str
    references: str


@dataclass
class MonthWeekInfo:
    """Information about a week within a month."""
    year: int
    month: str  # "Januari", "Februari", etc.
    month_number: int  # 1-12
    week_in_month: int  # 1, 2, 3, 4
    calendar_week: int  # ISO week number
    date: Optional[date]
    is_study_week: bool
    is_exam_week: bool = False
    is_holiday_week: bool = False
    exam_type: Optional[str] = None
    holiday_type: Optional[str] = None


@dataclass
class HolidayWeekBlock:
    """Represents a holiday block with exam week and holiday week."""
    holiday_type: str  # "midterm", "annual", "terminal", "midannual"
    exam_week: int  # ISO week number for exam
    holiday_weeks: List[int]  # Week numbers for holiday
    months_involved: List[str]
    start_date: date
    end_date: date
    language: str = "sw"

    # "midterm" is Muhula I's mid-term break, "midannual" is the
    # structurally equivalent mid-term break of Muhula II — labelled "I"
    # and "II" (matching the "Muhula wa I & II" convention already used
    # elsewhere in this document) so the two are distinguishable instead
    # of using unrelated Kiswahili terms ("Robo Muhula" vs "Nusu Muhula")
    # for the same kind of event.
    _EXAM_LABELS = {
        "sw": {
            "midterm": "MITIHANI YA ROBO MUHULA I",
            "midannual": "MITIHANI YA ROBO MUHULA II",
            "annual": "MITIHANI YA MWISHO WA MWAKA",
            "terminal": "MITIHANI YA MWISHO WA MUHULA",
        },
        "en": {
            "midterm": "FIRST MID-TERM EXAMINATIONS",
            "midannual": "SECOND MID-TERM EXAMINATIONS",
            "annual": "ANNUAL EXAMINATIONS",
            "terminal": "TERMINAL EXAMINATIONS",
        },
    }
    _HOLIDAY_LABELS = {
        "sw": {
            "midterm": "LIKIZO YA ROBO MUHULA I",
            "midannual": "LIKIZO YA ROBO MUHULA II",
            "annual": "LIKIZO YA MWISHO WA MWAKA",
            "terminal": "LIKIZO YA MWISHO WA MUHULA",
        },
        "en": {
            "midterm": "FIRST MID-TERM BREAK",
            "midannual": "SECOND MID-TERM BREAK",
            "annual": "ANNUAL BREAK",
            "terminal": "TERMINAL BREAK",
        },
    }

    @property
    def exam_label(self) -> str:
        """Get exam label based on type and language."""
        labels = self._EXAM_LABELS.get(self.language, self._EXAM_LABELS["sw"])
        return labels.get(self.holiday_type, "MTIHANI" if self.language == "sw" else "EXAMINATIONS")

    @property
    def holiday_label(self) -> str:
        """Get holiday label based on type and language."""
        labels = self._HOLIDAY_LABELS.get(self.language, self._HOLIDAY_LABELS["sw"])
        return labels.get(self.holiday_type, "LIKIZO" if self.language == "sw" else "BREAK")

    @property
    def date_range_label(self) -> str:
        """Get date range label in the requested language."""
        start_str = self.start_date.strftime("%d/%m/%Y")
        end_str = self.end_date.strftime("%d/%m/%Y")
        if self.language == "en":
            return f"STARTING {start_str} UNTIL {end_str}"
        return f"Kuanzia tarehe {start_str} hadi tarehe {end_str}"


class SchemeTimelineBuilder:
    """
    Builds a full academic year Scheme of Work for a given SubjectVersion.
    Algorithm:
    1. Get real study weeks from CalendarService (from actual AnnualCalendar dates)
    2. Subtract real exam weeks (derived from break blocks, not a fixed guess)
    3. Get total periods needed from syllabus activities
    4. Get periods per week from subject
    5. Calculate required weeks (total periods ÷ periods per week)
    6. Compare available weeks vs required weeks
    7. Distribute topics to fit available weeks, using each week's real month
       and real week-in-month position
    """

    # Muhtasari guidance: periods/week may be reduced to spread thin content
    # across more of the year, but never below 75% of the nominal rate.
    MIN_PERIODS_PER_WEEK_RATIO = 0.75

    # For a normal (non exam-prep) class, MARUDIO exists to give the class
    # a short revision tail, not to fill however many weeks happen to be
    # left over once the syllabus is exhausted at the (already-reduced)
    # effective pace - a scheme with 8+ weeks of generic "MARUDIO" rows is
    # not a real teaching plan. When more than this many weeks would be
    # left over, real topic periods are stretched (see
    # _adjust_periods_for_available_weeks) to fill the difference instead,
    # so only a short, genuine revision tail remains. National-exam class
    # levels are exempt - their long post-syllabus stretch is a deliberate,
    # dedicated exam-prep period, not overflow filler.
    MAX_MARUDIO_WEEKS = 3

    # DRS IV/VI/VII sit national exams — their syllabus content must be
    # forced to complete by end of August so the remaining term is spent on
    # MARUDIO (revision) and MAANDALIZI YA MTIHANI WA TAIFA (national exam
    # prep) instead of new topics. DRS VI only starts sitting the national
    # exam from academic year 2026 onward, so for 2025 it still gets the
    # normal full-year distribution.
    NATIONAL_EXAM_CLASS_LEVELS = {"DRS IV", "DRS VII"}
    NATIONAL_EXAM_CLASS_LEVEL_YEAR_GATES = {"DRS VI": 2026}
    NATIONAL_EXAM_CONTENT_CUTOFF_MONTH = 8  # August
    NATIONAL_EXAM_CONTENT_CUTOFF_DAY = 31

    # When August-cutoff mode must reduce a topic's real muhtasari period
    # count to fit the shortened Jan-Aug week budget, no topic may drop
    # below this fraction of its original periods (e.g. a topic that
    # needed 6 periods keeps at least 3) — periods/week itself stays at
    # the nominal rate rather than being raised.
    EXAM_PREP_MIN_PERIOD_RATIO = 0.5

    def __init__(
        self,
        competence_tree: dict,
        calendar_service: CalendarService,
        teacher_info: dict,
        subject_info: dict,
    ):
        self.tree = competence_tree
        self.calendar_service = calendar_service
        self.teacher_info = teacher_info
        self.subject_info = subject_info

        # Language handling — every builder-authored string (month names,
        # MARUDIO/exam-prep filler content, activity-field fallback
        # defaults) is sourced from the matching i18n module so English
        # subject_versions render fully in English, not just the labels
        # that happen to come from the request.
        self.language = subject_info.get("language", "sw")
        self._i18n = sw_i18n if self.language == "sw" else en_i18n
        self.month_names = self._i18n.MONTH_NAMES

        # Extract activities from competence tree
        self.activities = self._extract_activities()
        self.total_periods_needed = sum(a.periods_needed for a in self.activities)
        
        # Get periods per week from subject
        self.periods_per_week = subject_info.get("periods_per_week", 1)

        # DRS IV/VI(from 2026)/VII must finish content by end of August —
        # see NATIONAL_EXAM_CLASS_LEVELS above. Computed before
        # _calculate_available_study_weeks() since it caps the content
        # budget for these class levels.
        self.requires_exam_prep = self._requires_national_exam_prep()

        # Real date ranges (exam period through the day before each break
        # starts) that must never receive new content — applies to every
        # scheme, not just exam-prep mode, since schools close for holiday
        # right after exams regardless of class level.
        self.pre_break_exclusion_ranges = calendar_service.get_pre_break_exclusion_ranges()

        # Calculate calendar info
        self.total_learning_days = calendar_service.total_learning_days()
        self.available_study_weeks = self._calculate_available_study_weeks()
        
        # Identify holiday blocks
        self.holiday_blocks = self._identify_holiday_blocks()
        self.exam_weeks = self._identify_exam_weeks()
        
        # Calculate required weeks
        self.required_weeks = self._calculate_required_weeks()

        # Effective (actually used) periods/week: when the syllabus's total
        # periods don't fill the available study weeks at the nominal
        # muhtasari-specified rate, spread content more thinly (lower
        # periods/week) to reduce empty/revision weeks — but never drop
        # below MIN_PERIODS_PER_WEEK_RATIO (75%) of the nominal rate, per
        # muhtasari guidance. When there's MORE content than the nominal
        # rate can cover, effective stays at the nominal ceiling and
        # _adjust_periods_for_available_weeks() reduces activity periods
        # instead of exceeding the timetabled periods/week.
        self.effective_periods_per_week = self._calculate_effective_periods_per_week()

        logger.info(f"✅ SchemeTimelineBuilder initialized:")
        logger.info(f"   📚 Subject: {subject_info.get('subject_name')}")
        logger.info(f"   👥 Class: {subject_info.get('class_level_name')}")
        logger.info(f"   📅 Learning days: {self.total_learning_days}")
        logger.info(f"   📅 Available study weeks: {self.available_study_weeks}")
        logger.info(f"   📊 Total periods needed: {self.total_periods_needed}")
        logger.info(f"   📊 Periods per week: {self.periods_per_week}")
        logger.info(f"   📊 Required weeks: {self.required_weeks:.1f}")
        logger.info(f"   🎯 Holiday blocks: {len(self.holiday_blocks)}")

    # ==================================================
    # CORE CALCULATIONS (ALGORITHM MPYA)
    # ==================================================
    
    def _requires_national_exam_prep(self) -> bool:
        """Whether this scheme should force its syllabus content to finish
        by end of August. Applies automatically to every eligible class
        level (national-exam classes: DRS IV, VII always; DRS VI only
        from academic year 2026 onward) — those classes must finish
        content early to leave real time for revision and mock exams
        before the national exam. A teacher can still explicitly opt out
        via force_exam_prep_schedule=False for a specific Azimio."""
        if self.subject_info.get("force_exam_prep_schedule", True) is False:
            return False

        return self._is_national_exam_class_level()

    def _is_national_exam_class_level(self) -> bool:
        """Whether this class level ever sits the national exam (regardless
        of whether the teacher has opted into the August cutoff)."""
        class_level = (
            self.subject_info.get("class_level")
            or self.subject_info.get("class_level_name")
            or ""
        ).strip().upper()

        if class_level in self.NATIONAL_EXAM_CLASS_LEVELS:
            return True

        year_gate = self.NATIONAL_EXAM_CLASS_LEVEL_YEAR_GATES.get(class_level)
        if year_gate is not None:
            try:
                year = int(self.subject_info.get("year") or 0)
            except (TypeError, ValueError):
                year = 0
            return year >= year_gate

        return False

    def _is_excluded_date(self, d: date) -> bool:
        """Whether a real date falls in the exam-period-through-break-start
        window of any break block (see pre_break_exclusion_ranges)."""
        return any(start <= d <= end for start, end in self.pre_break_exclusion_ranges)

    def _calculate_available_study_weeks(self) -> int:
        """
        Real distinct ISO study-week numbers from the calendar, minus the
        real exam weeks (derived from the calendar's break blocks, not a
        fixed "6 weeks" guess) and any week that falls in the exam-to-break
        exclusion window. For national-exam class levels, only weeks up to
        end of August count toward the content budget — the rest of the
        year is reserved for revision/exam prep, not new topics.
        """
        studying_weeks = set(self.calendar_service.get_studying_weeks())
        exam_weeks = {
            w
            for weeks in self.calendar_service.get_exam_weeks_before_break().values()
            for w in weeks
        }
        studying_weeks = {
            w for w in studying_weeks
            if not (
                (real_date := self._find_date_for_iso_week(w))
                and self._is_excluded_date(real_date)
            )
        }

        if self.requires_exam_prep:
            cutoff = date(
                self.calendar_service.year,
                self.NATIONAL_EXAM_CONTENT_CUTOFF_MONTH,
                self.NATIONAL_EXAM_CONTENT_CUTOFF_DAY,
            )
            studying_weeks = {
                w for w in studying_weeks
                if (real_date := self._find_date_for_iso_week(w)) and real_date <= cutoff
            }

        available_weeks = len(studying_weeks - exam_weeks)

        # Ensure at least 1 week
        return max(available_weeks, 1)
    
    def _calculate_required_weeks(self) -> float:
        """
        Calculate weeks required to complete all syllabus topics.
        Formula: total_periods_needed ÷ periods_per_week
        """
        if self.periods_per_week <= 0:
            return 0
        
        required = self.total_periods_needed / self.periods_per_week
        return round(required, 1)

    def _calculate_effective_periods_per_week(self) -> float:
        """
        The subject's periods_per_week (self.periods_per_week) is the
        nominal muhtasari-specified rate (e.g. 6/week for Hisabati Std
        III-VI). If total_periods_needed doesn't fill available_study_weeks
        at that nominal rate, using the nominal rate anyway finishes the
        syllabus early and pads the rest of the year with generic MARUDIO
        (revision) weeks. Spreading the same content across more weeks at a
        lower rate is usually preferable — but per muhtasari guidance the
        rate must never drop below 75% of the nominal periods/week.
        """
        if self.available_study_weeks <= 0 or self.periods_per_week <= 0:
            return self.periods_per_week

        natural_rate = self.total_periods_needed / self.available_study_weeks
        if natural_rate >= self.periods_per_week:
            # Not enough weeks even at the nominal rate — keep the nominal
            # rate as the weekly ceiling (periods/week is a real timetable
            # allocation, it can't just be raised); activity periods get
            # reduced instead (see _adjust_periods_for_available_weeks).
            return self.periods_per_week

        floor_rate = self.periods_per_week * self.MIN_PERIODS_PER_WEEK_RATIO
        return max(natural_rate, floor_rate)

    def _adjust_periods_for_available_weeks(self) -> Tuple[List[Activity], float]:
        """
        Adjust activity periods if required weeks > available weeks.
        Returns: (adjusted_activities, periods_per_week_adjusted)
        """
        if self.required_weeks <= self.available_study_weeks:
            # Enough weeks at the nominal rate — use the (possibly lower,
            # floored at 75% of nominal) effective rate so content spreads
            # across more of the year instead of finishing early.
            effective_ppw = round(self.effective_periods_per_week, 1)

            # Even at the reduced effective pace, the syllabus may still
            # finish with far more than MAX_MARUDIO_WEEKS left over (e.g.
            # a light-content subject in a class with many study weeks).
            # For non exam-prep classes, stretch every activity's periods
            # proportionally so real topic content fills the year down to
            # a short revision tail, instead of leaving a long run of
            # generic MARUDIO filler weeks.
            if not self.requires_exam_prep and effective_ppw > 0 and self.total_periods_needed > 0:
                # Must match _create_study_weeks_schedule()'s own rounding
                # exactly (it allocates round(effective_periods_per_week)
                # whole periods per real study week) - using a different
                # precision here would compute a capacity ceiling that
                # doesn't match what the distributor can actually place.
                weekly_capacity = max(1, round(self.effective_periods_per_week))
                target_content_weeks = self.available_study_weeks - self.MAX_MARUDIO_WEEKS
                target_total_periods = target_content_weeks * weekly_capacity

                if target_total_periods > self.total_periods_needed:
                    stretch_ratio = target_total_periods / self.total_periods_needed

                    # Largest-remainder apportionment: scaling every
                    # activity independently and rounding each one (up or
                    # down) drifts the summed total away from
                    # target_total_periods - with enough small activities
                    # that drift can overshoot the real weekly capacity by
                    # a lot, and _distribute_activities_to_weeks() silently
                    # drops whatever doesn't fit in the last week rather
                    # than erroring. Floor every activity first (keeping at
                    # least 1 period each so no topic vanishes), then hand
                    # out the remaining budget one period at a time to the
                    # activities with the largest fractional remainder,
                    # so the summed total lands exactly on budget.
                    exact = [a.periods_needed * stretch_ratio for a in self.activities]
                    floored = [max(1, math.floor(x)) for x in exact]
                    remainder_budget = max(0, round(target_total_periods) - sum(floored))
                    order = sorted(
                        range(len(exact)),
                        key=lambda i: exact[i] - math.floor(exact[i]),
                        reverse=True,
                    )
                    for i in order[:remainder_budget]:
                        floored[i] += 1

                    stretched_activities = [
                        Activity(
                            index=a.index,
                            main_competence=a.main_competence,
                            main_order=a.main_order,
                            specific_competence=a.specific_competence,
                            specific_order=a.specific_order,
                            learning_activity=a.learning_activity,
                            learning_order=a.learning_order,
                            specific_learning=a.specific_learning,
                            specific_learning_order=a.specific_learning_order,
                            periods_needed=periods,
                            method=a.method,
                            assessment_criteria=a.assessment_criteria,
                            teaching_aids=a.teaching_aids,
                            references=a.references,
                        )
                        for a, periods in zip(self.activities, floored)
                    ]
                    stretched_total = sum(floored)
                    logger.info(
                        f"🔧 Stretched periods to cap MARUDIO at {self.MAX_MARUDIO_WEEKS} weeks: "
                        f"{self.total_periods_needed} → {stretched_total} "
                        f"(target {round(target_total_periods)}, x{round(stretch_ratio, 2)})"
                    )
                    return stretched_activities, effective_ppw

            return self.activities, effective_ppw

        # Not enough weeks, need to adjust
        logger.warning(f"⚠️ Not enough weeks! Required: {self.required_weeks}, Available: {self.available_study_weeks}")

        # Calculate total periods that can fit
        total_possible_periods = self.available_study_weeks * self.periods_per_week

        if total_possible_periods >= self.total_periods_needed:
            # Can fit all periods, just adjust periods per week
            adjusted_ppw = self.total_periods_needed / self.available_study_weeks
            return self.activities, round(adjusted_ppw, 1)

        # Cannot fit all periods, need to reduce
        reduction_ratio = total_possible_periods / self.total_periods_needed
        adjusted_activities = []

        for activity in self.activities:
            # Reduce periods proportionally, but ensure at least 1 period.
            # In August-cutoff mode, per the muhtasari-preservation rule, no
            # topic may drop below EXAM_PREP_MIN_PERIOD_RATIO (50%) of its
            # real muhtasari period count — e.g. a topic that needed 6
            # periods keeps at least 3 — even if that means the reduction
            # doesn't perfectly land on total_possible_periods.
            original_periods = activity.periods_needed
            if self.requires_exam_prep:
                min_periods = max(1, round(original_periods * self.EXAM_PREP_MIN_PERIOD_RATIO))
                adjusted_periods = max(min_periods, round(original_periods * reduction_ratio))
            else:
                adjusted_periods = max(1, math.floor(original_periods * reduction_ratio))

            adjusted_activity = Activity(
                index=activity.index,
                main_competence=activity.main_competence,
                main_order=activity.main_order,
                specific_competence=activity.specific_competence,
                specific_order=activity.specific_order,
                learning_activity=activity.learning_activity,
                learning_order=activity.learning_order,
                specific_learning=activity.specific_learning,
                specific_learning_order=activity.specific_learning_order,
                periods_needed=adjusted_periods,
                method=activity.method,
                assessment_criteria=activity.assessment_criteria,
                teaching_aids=activity.teaching_aids,
                references=activity.references,
            )
            adjusted_activities.append(adjusted_activity)
        
        adjusted_total = sum(a.periods_needed for a in adjusted_activities)
        adjusted_ppw = adjusted_total / self.available_study_weeks
        
        logger.info(f"🔧 Adjusted periods: {self.total_periods_needed} → {adjusted_total}")
        logger.info(f"🔧 Adjusted periods per week: {self.periods_per_week} → {round(adjusted_ppw, 1)}")
        
        return adjusted_activities, round(adjusted_ppw, 1)
    
    # ==================================================
    # ACTIVITY EXTRACTION
    # ==================================================
    
    def _extract_activities(self) -> List[Activity]:
        """Extract activities from competence tree."""
        activities = []
        
        logger.info("📚 Extracting activities from competence tree...")
        
        if not self.tree:
            raise ValueError(
                "Cannot build a scheme: no competence tree was provided "
                "(empty AnnualCalendar/competence data). Seed real syllabus "
                "content before generating a scheme."
            )

        # Get activities directly from tree
        tree_activities = self.tree.get("activities", [])

        if not tree_activities:
            logger.warning("No activities in tree, checking competences structure")
            return self._extract_from_competences_structure()
        
        # Process activities from tree
        for idx, activity_data in enumerate(tree_activities):
            try:
                activity = Activity(
                    index=idx + 1,
                    main_competence=activity_data.get("main_competence", ""),
                    main_order=activity_data.get("main_order", 0),
                    specific_competence=activity_data.get("specific_competence", ""),
                    specific_order=activity_data.get("specific_order", 0),
                    learning_activity=activity_data.get("learning_activity", ""),
                    learning_order=activity_data.get("learning_order", 0),
                    specific_learning=activity_data.get("specific_learning", ""),
                    specific_learning_order=activity_data.get("specific_learning_order", 0),
                    periods_needed=activity_data.get("periods_needed", 1),
                    method=activity_data.get("method", self._i18n.ACTIVITY_FIELD_DEFAULTS["method"]),
                    assessment_criteria=activity_data.get("assessment_criteria", self._i18n.ACTIVITY_FIELD_DEFAULTS["assessment_criteria"]),
                    teaching_aids=activity_data.get("teaching_aids", self._i18n.ACTIVITY_FIELD_DEFAULTS["teaching_aids"]),
                    references=activity_data.get("references", self._i18n.ACTIVITY_FIELD_DEFAULTS["references"]),
                )
                activities.append(activity)
            except Exception as e:
                logger.error(f"Error creating activity: {str(e)}")
        
        logger.info(f"✅ Extracted {len(activities)} activities")
        return activities
    
    def _extract_from_competences_structure(self) -> List[Activity]:
        """Fallback: Extract from competences structure."""
        activities = []
        main_competences = self.tree.get("competences", [])

        if not main_competences:
            raise ValueError(
                "Cannot build a scheme: no learning activities and no "
                "competences were found for this subject version. Seed real "
                "syllabus content before generating a scheme."
            )
        
        activity_index = 0
        for main_comp in sorted(main_competences, key=lambda x: x.get("order", 0)):
            main_name = main_comp.get("name", "")
            
            for spec_comp in main_comp.get("specific_competences", []):
                spec_name = spec_comp.get("name", "")
                
                for learn_act in spec_comp.get("learning_activities", []):
                    learn_name = learn_act.get("name", "")
                    
                    for spec_act in learn_act.get("specific_learning_activities", []):
                        activity_index += 1
                        activity = Activity(
                            index=activity_index,
                            main_competence=main_name,
                            main_order=main_comp.get("order", 0),
                            specific_competence=spec_name,
                            specific_order=spec_comp.get("order", 0),
                            learning_activity=learn_name,
                            learning_order=learn_act.get("order", 0),
                            specific_learning=spec_act.get("name", ""),
                            specific_learning_order=spec_act.get("order", 0),
                            periods_needed=spec_act.get("periods", 1),
                            method=spec_act.get("method", self._i18n.ACTIVITY_FIELD_DEFAULTS["method"]),
                            assessment_criteria=spec_act.get("assessment_criteria", self._i18n.ACTIVITY_FIELD_DEFAULTS["assessment_criteria"]),
                            teaching_aids=spec_act.get("teaching_aids", self._i18n.ACTIVITY_FIELD_DEFAULTS["teaching_aids"]),
                            references=spec_act.get("references", self._i18n.ACTIVITY_FIELD_DEFAULTS["references"]),
                        )
                        activities.append(activity)
        
        return activities
    
    # ==================================================
    # HOLIDAY AND EXAM IDENTIFICATION
    # ==================================================

    def _find_date_for_iso_week(self, iso_week: int) -> Optional[date]:
        """Find the real calendar date for an ISO week number, searching
        across all calendar blocks (study and break)."""
        for block in self.calendar_service.get_blocks():
            if iso_week not in block.week_numbers:
                continue
            current = block.start_date
            while current <= block.end_date:
                if current.isocalendar()[1] == iso_week:
                    return current
                current += timedelta(days=1)
        return None

    def _week_in_month_for_iso_week(self, iso_week: int) -> int:
        """Real 1-4 week-in-month position for an ISO week, based on its
        actual calendar date (not a synthetic 4-week grid)."""
        real_date = self._find_date_for_iso_week(iso_week)
        if real_date is None:
            return 1
        return min(((real_date.day - 1) // 7) + 1, 4)

    def _identify_holiday_blocks(self) -> List[HolidayWeekBlock]:
        """Identify holiday blocks with their weeks, using real calendar
        dates for exam-week and month derivation instead of magic numbers."""
        holiday_blocks = []

        try:
            break_blocks = self.calendar_service.get_break_blocks_with_names()
            exam_weeks_by_block = self.calendar_service.get_exam_weeks_before_break()

            for block in break_blocks:
                holiday_type = block.get('holiday_type', 'terminal')
                week_numbers = block.get('week_numbers', [])

                if not week_numbers:
                    continue

                # Real exam week(s) computed from the calendar (2 weeks
                # before an annual break, 1 week before other breaks) —
                # see CalendarService.get_exam_weeks_before_break().
                block_exam_weeks = exam_weeks_by_block.get(block.get('block_name', ''), [])
                exam_week = max(block_exam_weeks) if block_exam_weeks else 0

                # Get months involved from the block's real date range
                months = self._get_months_for_range(
                    date.fromisoformat(block['start_date']),
                    date.fromisoformat(block['end_date']),
                )

                holiday_block = HolidayWeekBlock(
                    holiday_type=holiday_type,
                    exam_week=exam_week,
                    holiday_weeks=week_numbers,
                    months_involved=months,
                    start_date=date.fromisoformat(block['start_date']),
                    end_date=date.fromisoformat(block['end_date']),
                    language=self.language,
                )

                holiday_blocks.append(holiday_block)
                logger.info(f"✅ Holiday block: {holiday_type} - Exam week: {exam_week}, Holiday weeks: {len(week_numbers)}")

        except Exception as e:
            logger.error(f"Error identifying holiday blocks: {str(e)}")

        return holiday_blocks

    def _identify_exam_weeks(self) -> List[int]:
        """Get all real exam weeks derived from the calendar's break blocks."""
        exam_weeks_by_block = self.calendar_service.get_exam_weeks_before_break()
        exam_weeks = sorted({w for weeks in exam_weeks_by_block.values() for w in weeks})
        logger.info(f"📝 Exam weeks identified: {exam_weeks}")
        return exam_weeks

    def _get_months_for_range(self, start_date: date, end_date: date) -> List[str]:
        """Get the real month names spanned by a date range, in
        chronological order."""
        months: List[str] = []
        seen = set()
        current = start_date.replace(day=1)
        while current <= end_date:
            if current.month not in seen:
                seen.add(current.month)
                month_label = "Month" if self.language == "en" else "Mwezi"
                months.append(self.month_names.get(current.month, f"{month_label} {current.month}"))
            # advance to the first of the next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return months
    
    # ==================================================
    # WEEK DISTRIBUTION ALGORITHM
    # ==================================================
    
    def _create_study_weeks_schedule(self) -> List[Dict]:
        """
        Create schedule of study weeks with their periods, walking the real
        calendar (in chronological order) instead of a synthetic 4-weeks-
        per-month grid. Returns list of weeks with: {
            "week_number": int (1-based, sequential),
            "iso_week_number": int (real ISO week from the calendar),
            "week_in_month": int (real position within its real month),
            "month": str (real month name),
            "periods_allocated": int,
            "is_exam": bool,
            "is_holiday": bool
        }
        """
        schedule = []
        week_counter = 0

        exam_week_numbers = set(w for w in self.exam_weeks if w > 0)

        seen_weeks = set()
        for block in self.calendar_service.get_study_blocks():
            for iso_week in block.week_numbers:
                if iso_week in seen_weeks:
                    continue
                seen_weeks.add(iso_week)

                real_date = self._find_date_for_iso_week(iso_week)

                # Exclude both the labeled exam week AND any real date that
                # falls between the exam period and the break's actual
                # start (see pre_break_exclusion_ranges) — schools stop new
                # teaching once exams start, not just for the single ISO
                # week the exam is labeled on.
                is_exam = iso_week in exam_week_numbers or (
                    real_date is not None and self._is_excluded_date(real_date)
                )
                # NOTE: don't also exclude weeks in break_week_numbers here.
                # We're already iterating get_study_blocks() exclusively, so
                # a week only shows up at all because it's real teaching
                # time; break_week_numbers is a whole-calendar set that can
                # share an ISO week number with an adjacent study block at a
                # term-transition boundary (e.g. a break starting mid-week),
                # and blanket-excluding those wrongly zeroed out a real
                # teaching week every time two blocks met — that's what
                # made the real weekly supply (~27) fall well short of the
                # formula-derived available_study_weeks (~37), pushing
                # content much further into the year than it needed to.
                is_holiday = False

                month_name = self.month_names.get(
                    real_date.month if real_date else 1, self.month_names[1]
                )
                week_in_month = self._week_in_month_for_iso_week(iso_week)

                # Only allocate periods to real study weeks (not exam weeks).
                # Uses effective_periods_per_week (nominal rate, or lower
                # when spreading thin content — floored at 75% of nominal)
                # rather than the raw nominal rate. Stays at the nominal
                # rate for August-cutoff mode too — periods/week reflects a
                # real timetable allocation and can't just be raised; see
                # _adjust_periods_for_available_weeks() for how content is
                # instead fitted into the shortened week budget.
                periods_allocated = 0
                if not is_exam and not is_holiday:
                    week_counter += 1
                    periods_allocated = max(1, round(self.effective_periods_per_week))

                schedule.append({
                    "week_number": week_counter or (len(schedule) + 1),
                    "iso_week_number": iso_week,
                    "week_in_month": week_in_month,
                    "month": month_name,
                    "periods_allocated": periods_allocated,
                    "is_exam": is_exam,
                    "is_holiday": is_holiday,
                    "cumulative_weeks": week_counter,
                })

        # Deliberately walk every real study week in the calendar (no early
        # break once week_counter reaches available_study_weeks): for
        # national-exam class levels, available_study_weeks is capped to
        # the Jan-Aug content budget, but weeks after that cutoff still
        # need to appear here (with periods_allocated set) so
        # _distribute_activities_to_weeks() can fill them with revision /
        # exam-prep instead of silently dropping them from the document.
        logger.info(f"📅 Created schedule: {len(schedule)} weeks ({week_counter} allocatable)")
        return schedule
    
    def _distribute_activities_to_weeks(self, activities: List[Activity], 
                                       weeks_schedule: List[Dict]) -> List[ScheduleItem]:
        """
        Distribute activities to study weeks.
        """
        items = []
        
        if not activities or not weeks_schedule:
            logger.error("No activities or weeks to distribute")
            return items
        
        activity_idx = 0
        current_activity = None
        remaining_periods = 0
        weeks_consumed = 0

        # Get study weeks only (not exam/holiday)
        study_weeks = [w for w in weeks_schedule if w["periods_allocated"] > 0]

        for week in study_weeks:
            weekly_capacity = week["periods_allocated"]
            periods_used = 0
            weeks_consumed += 1

            while periods_used < weekly_capacity and activity_idx < len(activities):
                # Get next activity if needed
                if current_activity is None:
                    current_activity = activities[activity_idx]
                    remaining_periods = current_activity.periods_needed
                
                # Calculate periods for this week
                periods_to_use = min(remaining_periods, weekly_capacity - periods_used)
                
                if periods_to_use > 0:
                    # Create schedule item
                    item = create_merged_schedule_item(
                        months=[week["month"]],
                        weeks=[week["week_in_month"]],
                        total_periods=periods_to_use,
                        main_competence=current_activity.main_competence,
                        specific_competence=current_activity.specific_competence,
                        learning_activity=current_activity.learning_activity,
                        student_activity=current_activity.specific_learning,
                        methodology=current_activity.method,
                        assessment_criteria=current_activity.assessment_criteria,
                        teaching_aids=current_activity.teaching_aids,
                        references=current_activity.references,
                        week_date=self._find_date_for_iso_week(week["iso_week_number"]),
                        # MAONI is left blank for the teacher to fill in by
                        # hand — it isn't ours to pre-populate.
                        remarks=""
                    )
                    items.append(item)
                    
                    periods_used += periods_to_use
                    remaining_periods -= periods_to_use
                
                # Move to next activity if done
                if remaining_periods == 0:
                    current_activity = None
                    activity_idx += 1
            
            # Break if all activities are distributed
            if activity_idx >= len(activities):
                break
        
        # Fill any remaining real study weeks with revision (MARUDIO) items,
        # using each remaining week's own real month/week-in-month rather
        # than inventing a synthetic month/week sequence. For national-exam
        # class levels (DRS IV/VI/VII), the final stretch of leftover weeks
        # — closer to the national exam — is labelled as dedicated exam
        # prep (MAANDALIZI YA MTIHANI WA TAIFA) instead of generic revision.
        leftover_weeks = study_weeks[weeks_consumed:]

        exam_prep_weeks: set = set()
        if self.requires_exam_prep and leftover_weeks:
            exam_prep_count = max(2, len(leftover_weeks) // 3)
            exam_prep_weeks = {
                w["iso_week_number"] for w in leftover_weeks[-exam_prep_count:]
            }

        for week in leftover_weeks:
            content = (
                self._i18n.EXAM_PREP_CONTENT
                if week["iso_week_number"] in exam_prep_weeks
                else self._i18n.MARUDIO_CONTENT
            )
            revision_item = create_merged_schedule_item(
                months=[week["month"]],
                weeks=[week["week_in_month"]],
                total_periods=week["periods_allocated"],
                main_competence=content["main_competence"],
                specific_competence=content["specific_competence"],
                learning_activity=content["learning_activity"],
                student_activity=content["student_activity"],
                methodology=content["methodology"],
                assessment_criteria=content["assessment_criteria"],
                teaching_aids=content["teaching_aids"],
                references=content["references"],
                week_date=self._find_date_for_iso_week(week["iso_week_number"]),
                remarks=""
            )
            items.append(revision_item)

        logger.info(f"✅ Distributed {len(items)} activity items")
        return items
    
    # ==================================================
    # MAIN BUILD METHOD
    # ==================================================
    
    def build(self, balance_weekly: bool = True) -> SchemeData:
        """
        Build complete Scheme of Work following the new algorithm.
        """
        logger.info(f"🏗️ Building scheme with new algorithm...")
        
        # Step 1: Adjust periods if needed
        adjusted_activities, adjusted_ppw = self._adjust_periods_for_available_weeks()
        
        # Step 2: Create weeks schedule
        weeks_schedule = self._create_study_weeks_schedule()
        
        # Step 3: Distribute activities to weeks
        teaching_items = self._distribute_activities_to_weeks(adjusted_activities, weeks_schedule)
        
        # Step 4: Create holiday block items
        holiday_items = self._create_holiday_block_items()

        # Combine and sort chronologically (by each item's real calendar
        # date) so holiday/exam rows appear inline where they actually
        # fall in the year instead of all being dumped after every
        # teaching row. Stable sort keeps same-date ties in their
        # original relative order.
        all_items = teaching_items + holiday_items
        all_items.sort(key=lambda item: item.week_date or date.max)
        
        # Step 5: Calculate period statistics
        total_periods_allocated = sum(item.periods for item in teaching_items)
        available_periods = self.available_study_weeks * adjusted_ppw
        period_difference = available_periods - total_periods_allocated
        
        # Step 6: Create identification
        identification = SchemeIdentification(
            teacher_name=self.teacher_info.get("teacher_name", ""),
            school_name=self.teacher_info.get("school_name", ""),
            language=self.language,
        )
        
        # Step 7: Create period calculation
        period_calculation = PeriodCalculation(
            total_periods=total_periods_allocated,
            periods_per_week=adjusted_ppw,
            required_weeks=self.required_weeks,
            available_weeks=self.available_study_weeks,
            available_periods=available_periods,
            period_difference=period_difference,
            distribution_ratio=total_periods_allocated / available_periods if available_periods > 0 else 0,
            adjusted_periods_per_week=adjusted_ppw,
        )
        
        # Step 8: Create final scheme data
        scheme_data = SchemeData(
            council=self.teacher_info.get("council", ""),
            ward=self.teacher_info.get("ward", ""),
            school_name=self.teacher_info.get("school_name", ""),
            teacher_name=self.teacher_info.get("teacher_name", ""),
            
            subject_name=self.subject_info.get("subject_name", ""),
            class_level_name=self.subject_info.get("class_level_name", ""),
            year=self.subject_info.get("year", ""),
            term=self.subject_info.get("term", ""),
            term_display=self.subject_info.get("term_display", ""),
            
            objectives=self.subject_info.get("objectives", []),
            headers=self._i18n.SCHEME_LABELS["headers"],
            
            calendar_data=self.calendar_service.to_dict(),
            period_calculation=period_calculation,
            schedule_items=all_items,
            identification=identification,
        )
        
        # Log summary
        logger.info(f"✅ SCHEME BUILT SUCCESSFULLY")
        logger.info(f"   📊 Total items: {len(all_items)}")
        logger.info(f"   📊 Teaching items: {len(teaching_items)}")
        logger.info(f"   📊 Holiday items: {len(holiday_items)}")
        logger.info(f"   📊 Total periods: {total_periods_allocated}")
        logger.info(f"   📊 Periods per week: {adjusted_ppw}")
        logger.info(f"   📊 Available weeks: {self.available_study_weeks}")
        logger.info(f"   📊 Period balance: {period_difference}")
        
        return scheme_data
    
    def _create_holiday_block_items(self) -> List[ScheduleItem]:
        """Create holiday block items (exam + holiday + date range)."""
        holiday_items = []
        
        for block in self.holiday_blocks:
            # Exam week row — the exam week is *before* the break block, so
            # its real date (and therefore month) can fall in an earlier
            # month than the break itself (e.g. a break starting in April
            # can have its exam week in late March). Use the exam week's
            # own real date for both month and week-in-month, not the
            # break block's month range.
            if block.exam_week and block.exam_week > 0:
                exam_date = self._find_date_for_iso_week(block.exam_week)
                exam_month = self.month_names.get(exam_date.month, block.months_involved[0]) if exam_date else block.months_involved[0]
                exam_item = create_merged_schedule_item(
                    months=[exam_month],
                    weeks=[self._week_in_month_for_iso_week(block.exam_week)],
                    total_periods=0,
                    student_activity=block.exam_label,
                    remarks="",
                    week_date=exam_date,
                    is_special=True,
                    row_type="exam"
                )
                holiday_items.append(exam_item)

            # Holiday weeks row — label and date range merged into a single
            # row (they describe the same holiday block), matching the real
            # reference documents ("LIKIZO FUPI KUANZIA {date} HADI {date}")
            # instead of two separate rows for the same information.
            if block.holiday_weeks:
                # Group holiday weeks for display (real week-in-month positions)
                sorted_holiday_weeks = sorted(block.holiday_weeks)[:3]
                week_display = [
                    self._week_in_month_for_iso_week(w)
                    for w in sorted_holiday_weeks
                ]
                merged_label = f"{block.holiday_label} {block.date_range_label}"
                holiday_item = create_merged_schedule_item(
                    months=block.months_involved,
                    weeks=week_display,
                    total_periods=0,
                    student_activity=merged_label,
                    remarks="",
                    week_date=block.start_date,
                    is_special=True,
                    row_type="holiday"
                )
                holiday_items.append(holiday_item)
        
        return holiday_items
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics."""
        return {
            "subject": self.subject_info.get("subject_name"),
            "class_level": self.subject_info.get("class_level_name"),
            "total_activities": len(self.activities),
            "total_periods_needed": self.total_periods_needed,
            "periods_per_week": self.periods_per_week,
            "effective_periods_per_week": round(self.effective_periods_per_week, 1),
            "total_learning_days": self.total_learning_days,
            "available_study_weeks": self.available_study_weeks,
            "required_weeks": self.required_weeks,
            "week_balance": self.available_study_weeks - self.required_weeks,
            "holiday_blocks": len(self.holiday_blocks),
            "exam_weeks": len([w for w in self.exam_weeks if w > 0]),
        }