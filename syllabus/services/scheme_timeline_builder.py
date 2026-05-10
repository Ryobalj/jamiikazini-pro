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
    
    @property
    def exam_label(self) -> str:
        """Get exam label based on type."""
        labels = {
            "midterm": "MITIHANI YA ROBO MUHULA",
            "midannual": "MITIHANI YA NUSU MUHULA",
            "annual": "MITIHANI YA MWISHO WA MWAKA",
            "terminal": "MITIHANI YA MWISHO WA MUHULA"
        }
        return labels.get(self.holiday_type, "MTIHANI")
    
    @property
    def holiday_label(self) -> str:
        """Get holiday label based on type."""
        labels = {
            "midterm": "LIKIZO YA ROBO MUHULA",
            "midannual": "LIKIZO YA NUSU MUHULA",
            "annual": "LIKIZO YA MWISHO WA MWAKA",
            "terminal": "LIKIZO YA MWISHO WA MUHULA"
        }
        return labels.get(self.holiday_type, "LIKIZO")
    
    @property
    def date_range_label(self) -> str:
        """Get date range label."""
        start_str = self.start_date.strftime("%d/%m/%Y")
        end_str = self.end_date.strftime("%d/%m/%Y")
        return f"Kuanzia tarehe {start_str} hadi tarehe {end_str}"


class SchemeTimelineBuilder:
    """
    Builds a full academic year Scheme of Work for a given SubjectVersion.
    Algorithm:
    1. Get total learning days from calendar
    2. Convert to study weeks (÷ 5 days)
    3. Subtract exam weeks (6 weeks)
    4. Get total periods needed from syllabus activities
    5. Get periods per week from subject
    6. Calculate required weeks (total periods ÷ periods per week)
    7. Compare available weeks vs required weeks
    8. Distribute topics to fit available weeks
    """
    
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

        # Language handling
        self.language = subject_info.get("language", "sw")
        
        # Extract activities from competence tree
        self.activities = self._extract_activities()
        self.total_periods_needed = sum(a.periods_needed for a in self.activities)
        
        # Get periods per week from subject
        self.periods_per_week = subject_info.get("periods_per_week", 1)
        
        # Calculate calendar info
        self.total_learning_days = calendar_service.total_learning_days()
        self.available_study_weeks = self._calculate_available_study_weeks()
        
        # Identify holiday blocks
        self.holiday_blocks = self._identify_holiday_blocks()
        self.exam_weeks = self._identify_exam_weeks()
        
        # Calculate required weeks
        self.required_weeks = self._calculate_required_weeks()
        
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
    
    def _calculate_available_study_weeks(self) -> int:
        """
        1. Get total learning days (Mon-Fri in study blocks)
        2. Convert to weeks (÷ 5 days)
        3. Subtract exam weeks (6 weeks total)
        """
        # Convert learning days to weeks
        total_weeks = math.floor(self.total_learning_days / 5)
        
        # Subtract exam weeks (6 weeks for the whole year)
        available_weeks = total_weeks - 6
        
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
    
    def _adjust_periods_for_available_weeks(self) -> Tuple[List[Activity], float]:
        """
        Adjust activity periods if required weeks > available weeks.
        Returns: (adjusted_activities, periods_per_week_adjusted)
        """
        if self.required_weeks <= self.available_study_weeks:
            # Enough weeks, return original
            return self.activities, self.periods_per_week
        
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
            # Reduce periods proportionally, but ensure at least 1 period
            original_periods = activity.periods_needed
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
            logger.warning("Empty competence tree, creating sample activities")
            return self._create_sample_activities()
        
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
                    method=activity_data.get("method", "Majadiliano na mazoezi"),
                    assessment_criteria=activity_data.get("assessment_criteria", "Ushiriki na mazoezi"),
                    teaching_aids=activity_data.get("teaching_aids", "Kadi, chati, kitabu"),
                    references=activity_data.get("references", "Kitabu cha mwanafunzi"),
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
            logger.error("No competences found, creating sample activities")
            return self._create_sample_activities()
        
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
                            method=spec_act.get("method", "Majadiliano na mazoezi"),
                            assessment_criteria=spec_act.get("assessment_criteria", "Ushiriki na mazoezi"),
                            teaching_aids=spec_act.get("teaching_aids", "Kadi, chati, kitabu"),
                            references=spec_act.get("references", "Kitabu cha mwanafunzi"),
                        )
                        activities.append(activity)
        
        return activities
    
    def _create_sample_activities(self) -> List[Activity]:
        """Create sample activities for testing."""
        samples = []
        sample_data = [
            ("Kuhesabu", "Kutambua namba 1-10", "Kutambua namba kwa vitu", "Kutambua namba 1-5", 2),
            ("Kuhesabu", "Kutambua namba 1-10", "Kutambua namba kwa vitu", "Kutambua namba 6-10", 2),
            ("Kuhesabu", "Kupanga namba 1-20", "Kupanga namba kwa mfuatano", "Kupanga namba 1-10", 3),
            ("Kuhesabu", "Kupanga namba 1-20", "Kupanga namba kwa mfuatano", "Kupanga namba 11-20", 3),
            ("Kuhesabu", "Kujumlisha namba", "Kutumia vitu kujumlisha", "Kujumlisha hadi 10", 4),
            ("Kuhesabu", "Kujumlisha namba", "Kutumia vitu kujumlisha", "Kujumlisha hadi 20", 4),
        ]
        
        for idx, (main, spec, learn, spec_learn, periods) in enumerate(sample_data):
            activity = Activity(
                index=idx + 1,
                main_competence=main,
                main_order=1,
                specific_competence=spec,
                specific_order=1,
                learning_activity=learn,
                learning_order=1,
                specific_learning=spec_learn,
                specific_learning_order=1,
                periods_needed=periods,
                method="Majadiliano na mazoezi",
                assessment_criteria="Ushiriki na mazoezi",
                teaching_aids="Kadi, chati, kitabu",
                references="Kitabu cha mwanafunzi",
            )
            samples.append(activity)
        
        return samples
    
    # ==================================================
    # HOLIDAY AND EXAM IDENTIFICATION
    # ==================================================
    
    def _identify_holiday_blocks(self) -> List[HolidayWeekBlock]:
        """Identify holiday blocks with their weeks."""
        holiday_blocks = []
        
        try:
            break_blocks = self.calendar_service.get_break_blocks_with_names()
            
            for block in break_blocks:
                holiday_type = block.get('holiday_type', 'terminal')
                week_numbers = block.get('week_numbers', [])
                
                if not week_numbers:
                    continue
                
                # Determine exam week (week before holiday starts)
                first_holiday_week = min(week_numbers)
                exam_week = first_holiday_week - 1 if first_holiday_week > 1 else None
                
                # For annual break, use specific weeks (49, 50 for exams)
                if holiday_type == "annual":
                    exam_week = 49  # Last exam week of the year
                    holiday_weeks = [w for w in week_numbers if w >= 50]
                else:
                    holiday_weeks = week_numbers
                
                # Get months involved
                months = self._get_months_for_weeks(holiday_weeks)
                
                holiday_block = HolidayWeekBlock(
                    holiday_type=holiday_type,
                    exam_week=exam_week if exam_week else 0,
                    holiday_weeks=holiday_weeks,
                    months_involved=months,
                    start_date=date.fromisoformat(block['start_date']),
                    end_date=date.fromisoformat(block['end_date'])
                )
                
                holiday_blocks.append(holiday_block)
                logger.info(f"✅ Holiday block: {holiday_type} - Exam week: {exam_week}, Holiday weeks: {len(holiday_weeks)}")
        
        except Exception as e:
            logger.error(f"Error identifying holiday blocks: {str(e)}")
        
        return holiday_blocks
    
    def _identify_exam_weeks(self) -> List[int]:
        """Get all exam weeks from holiday blocks."""
        exam_weeks = []
        for block in self.holiday_blocks:
            if block.exam_week and block.exam_week > 0:
                exam_weeks.append(block.exam_week)
        
        # Ensure we have 6 exam weeks total
        while len(exam_weeks) < 6:
            exam_weeks.append(0)  # Placeholder
        
        logger.info(f"📝 Exam weeks identified: {exam_weeks}")
        return exam_weeks
    
    def _get_months_for_weeks(self, week_numbers: List[int]) -> List[str]:
        """Get month names for given week numbers."""
        # This is simplified - in real implementation, use calendar service
        month_map = {
            1: "Januari", 2: "Februari", 3: "Machi", 4: "Aprili",
            5: "Mei", 6: "Juni", 7: "Julai", 8: "Agosti",
            9: "Septemba", 10: "Oktoba", 11: "Novemba", 12: "Desemba"
        }
        
        months = set()
        for week in week_numbers:
            # Simplified: week 1-4 = Jan, 5-8 = Feb, etc.
            month_num = min(((week - 1) // 4) + 1, 12)
            months.add(month_map.get(month_num, f"Mwezi {month_num}"))
        
        return sorted(list(months))
    
    # ==================================================
    # WEEK DISTRIBUTION ALGORITHM
    # ==================================================
    
    def _create_study_weeks_schedule(self) -> List[Dict]:
        """
        Create schedule of study weeks with their periods.
        Returns list of weeks with: {
            "week_number": int (1-based),
            "month": str,
            "periods_allocated": int,
            "is_exam": bool,
            "is_holiday": bool
        }
        """
        schedule = []
        week_counter = 1
        
        # Get all months in order
        months = ["Januari", "Februari", "Machi", "Aprili", "Mei", "Juni",
                  "Julai", "Agosti", "Septemba", "Oktoba", "Novemba", "Desemba"]
        
        # Distribute weeks across months
        weeks_per_month = 4  # Assume 4 weeks per month
        
        for month_idx, month_name in enumerate(months):
            for week_in_month in range(1, weeks_per_month + 1):
                if week_counter > self.available_study_weeks:
                    break
                
                # Check if this is an exam week
                is_exam = week_counter in [w for w in self.exam_weeks if w > 0]
                
                # Check if this is a holiday week
                is_holiday = False
                for block in self.holiday_blocks:
                    if week_counter in block.holiday_weeks:
                        is_holiday = True
                        break
                
                # Only allocate periods to study weeks (not exam/holiday)
                periods_allocated = 0
                if not is_exam and not is_holiday:
                    periods_allocated = self.periods_per_week
                
                schedule.append({
                    "week_number": week_counter,
                    "week_in_month": week_in_month,
                    "month": month_name,
                    "periods_allocated": periods_allocated,
                    "is_exam": is_exam,
                    "is_holiday": is_holiday,
                    "cumulative_weeks": week_counter
                })
                
                week_counter += 1
        
        logger.info(f"📅 Created schedule: {len(schedule)} weeks")
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
        
        # Get study weeks only (not exam/holiday)
        study_weeks = [w for w in weeks_schedule if w["periods_allocated"] > 0]
        
        for week in study_weeks:
            weekly_capacity = week["periods_allocated"]
            periods_used = 0
            
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
                        week_date=None,
                        remarks="Endelea" if remaining_periods > periods_to_use else "Imemalizika"
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
        
        # Add revision weeks if there are extra weeks
        extra_weeks = len(study_weeks) - len([i for i in items if i.periods > 0])
        if extra_weeks > 0:
            # Find last study week with content
            last_study_week = study_weeks[-1] if study_weeks else None
            
            if last_study_week:
                for i in range(extra_weeks):
                    revision_week_num = last_study_week["week_number"] + i + 1
                    revision_month = last_study_week["month"]
                    
                    # Add revision week
                    revision_item = create_merged_schedule_item(
                        months=[revision_month],
                        weeks=[revision_week_num % 4 or 4],
                        total_periods=self.periods_per_week,
                        main_competence="MARUDIO",
                        specific_competence="Kukagua na kufanya marudio",
                        learning_activity="Kukagua mada zilizofunzwa",
                        student_activity="Kufanya mazoezi ya marudio",
                        methodology="Majadiliano na mazoezi",
                        assessment_criteria="Ushiriki na usahihi",
                        teaching_aids="Kadi za mazoezi",
                        references="Vyanzo vya kumbukumbu",
                        week_date=None,
                        remarks="Wiki ya marudio"
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
        
        # Combine all items
        all_items = teaching_items + holiday_items
        
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
            headers=[
                "Umahiri Mkuu",
                "Umahiri Mahususi",
                "Shughuli za Ufundishaji",
                "Shughuli za Ujifunzaji",
                "Mwezi",
                "Wiki",
                "Vipindi",
                "Mbinu",
                "Marejeo",
                "Zana",
                "Vigezo vya Upimaji",
                "Maoni"
            ],
            
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
            # Exam week row
            if block.exam_week and block.exam_week > 0:
                exam_item = create_merged_schedule_item(
                    months=block.months_involved,
                    weeks=[block.exam_week % 4 or 4],
                    total_periods=0,
                    student_activity=block.exam_label,
                    remarks=block.exam_label,
                    is_special=True
                )
                holiday_items.append(exam_item)
            
            # Holiday weeks row
            if block.holiday_weeks:
                # Group holiday weeks for display
                week_display = sorted(block.holiday_weeks)[:3]  # Show first 3 weeks
                holiday_item = create_merged_schedule_item(
                    months=block.months_involved,
                    weeks=week_display,
                    total_periods=0,
                    student_activity=block.holiday_label,
                    remarks=block.holiday_label,
                    is_special=True
                )
                holiday_items.append(holiday_item)
            
            # Date range row
            date_item = create_merged_schedule_item(
                months=block.months_involved,
                weeks=[],  # Empty for date row
                total_periods=0,
                student_activity=block.date_range_label,
                remarks=block.date_range_label,
                is_special=True
            )
            holiday_items.append(date_item)
        
        return holiday_items
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics."""
        return {
            "subject": self.subject_info.get("subject_name"),
            "class_level": self.subject_info.get("class_level_name"),
            "total_activities": len(self.activities),
            "total_periods_needed": self.total_periods_needed,
            "periods_per_week": self.periods_per_week,
            "total_learning_days": self.total_learning_days,
            "available_study_weeks": self.available_study_weeks,
            "required_weeks": self.required_weeks,
            "week_balance": self.available_study_weeks - self.required_weeks,
            "holiday_blocks": len(self.holiday_blocks),
            "exam_weeks": len([w for w in self.exam_weeks if w > 0]),
        }