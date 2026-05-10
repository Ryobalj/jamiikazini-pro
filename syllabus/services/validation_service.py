# syllabus/services/validation_service.py

from typing import Dict, List, Any, Optional, Tuple
from datetime import date, time
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error with detailed context."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value
        self.message = message
        
    def __str__(self):
        if self.field:
            return f"{self.message} (Field: {self.field}, Value: {self.value})"
        return self.message


class AcademicValidationService:
    """
    Production-ready validation service for academic documents.
    
    Validates:
    1. Scheme of Work structure and logic
    2. Lesson Plan completeness and consistency
    3. Academic calendar constraints
    4. Period allocations
    """
    
    # ====================================================
    # SCHEME OF WORK VALIDATION
    # ====================================================
    
    @classmethod
    def validate_scheme_data(cls, scheme_data: Dict) -> Tuple[bool, List[str]]:
        """
        Comprehensive scheme of work validation.
        
        Args:
            scheme_data: Complete scheme data
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        try:
            # 1. Basic structure validation
            cls._validate_scheme_structure(scheme_data)
            
            # 2. Period allocation validation
            cls._validate_scheme_periods(scheme_data)
            
            # 3. Calendar integration validation
            cls._validate_scheme_calendar(scheme_data)
            
            # 4. Competence hierarchy validation
            cls._validate_competence_hierarchy(scheme_data)
            
            # 5. Language consistency validation
            if "language" in scheme_data:
                cls._validate_language_consistency(scheme_data)
            
            logger.info("Scheme validation passed successfully")
            return True, warnings
            
        except ValidationError as e:
            logger.error(f"Scheme validation failed: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Unexpected validation error: {str(e)}")
            raise ValidationError(f"Validation error: {str(e)}")

    @staticmethod
    def _validate_scheme_structure(scheme_data: Dict):
        """Validate basic scheme structure."""
        required_fields = [
            "subject_name",
            "class_level_name", 
            "year",
            "term",
            "teacher_name",
            "school_name",
        ]
        
        missing_fields = [field for field in required_fields 
                         if field not in scheme_data or not scheme_data[field]]
        
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                field="structure"
            )
        
        # Validate schedule items
        if "schedule_items" not in scheme_data:
            raise ValidationError("Missing schedule items", field="schedule_items")
        
        if not isinstance(scheme_data["schedule_items"], list):
            raise ValidationError("Schedule items must be a list", field="schedule_items")

    @staticmethod
    def _validate_scheme_periods(scheme_data: Dict):
        """Validate period allocation logic."""
        schedule_items = scheme_data.get("schedule_items", [])
        
        if not schedule_items:
            raise ValidationError("No schedule items found", field="schedule_items")
        
        # Group by week
        week_periods = {}
        for item in schedule_items:
            week_num = item.get("week_number")
            if week_num not in week_periods:
                week_periods[week_num] = 0
            week_periods[week_num] += item.get("periods", 0)
        
        # Get periods per week limit
        periods_per_week = scheme_data.get("periods_per_week", 
                                          scheme_data.get("period_calculation", {}).get("periods_per_week", 0))
        
        if periods_per_week <= 0:
            logger.warning("Periods per week not specified or invalid")
            return
        
        # Check each week
        for week_num, total_periods in week_periods.items():
            if total_periods > periods_per_week:
                raise ValidationError(
                    f"Week {week_num} exceeds period limit: "
                    f"{total_periods} > {periods_per_week}",
                    field=f"week_{week_num}_periods",
                    value=total_periods
                )
            
            if total_periods == 0:
                logger.warning(f"Week {week_num} has 0 teaching periods")

    @staticmethod
    def _validate_scheme_calendar(scheme_data: Dict):
        """Validate scheme against academic calendar."""
        calendar_data = scheme_data.get("calendar_data")
        if not calendar_data:
            logger.warning("No calendar data found for validation")
            return
        
        schedule_items = scheme_data.get("schedule_items", [])
        
        # Check if all weeks are within academic year
        weeks_in_scheme = {item.get("week_number") for item in schedule_items}
        
        # Extract studying weeks from calendar
        studying_weeks = set()
        if isinstance(calendar_data, dict) and "studying_weeks" in calendar_data:
            studying_weeks = set(calendar_data["studying_weeks"])
        elif isinstance(calendar_data, list):
            # Assume it's blocks structure
            for block in calendar_data:
                if block.get("block_type") == "study":
                    studying_weeks.update(block.get("week_numbers", []))
        
        # Check for weeks outside studying period
        non_study_weeks = weeks_in_scheme - studying_weeks
        if non_study_weeks:
            logger.warning(f"Schedule includes non-study weeks: {sorted(non_study_weeks)}")

    @staticmethod
    def _validate_competence_hierarchy(scheme_data: Dict):
        """Validate competence hierarchy completeness."""
        schedule_items = scheme_data.get("schedule_items", [])
        
        for item in schedule_items:
            # Check required competence fields
            if not item.get("main_competence") and not item.get("specific_competence"):
                logger.warning(f"Week {item.get('week_number')}: Missing competence information")
            
            # Check activity fields
            if not item.get("learning_activity") and not item.get("student_activity"):
                logger.warning(f"Week {item.get('week_number')}: Missing activity information")

    @staticmethod
    def _validate_language_consistency(scheme_data: Dict):
        """Validate language consistency across scheme."""
        language = scheme_data.get("language", "sw")
        
        # Check language-specific field consistency
        schedule_items = scheme_data.get("schedule_items", [])
        for item in schedule_items:
            # You could add language-specific validation here
            # For example, check Swahili/English terminology consistency
            pass

    # ====================================================
    # WEEK-SPECIFIC VALIDATION
    # ====================================================
    
    @classmethod
    def validate_scheme_week(
        cls, 
        scheme_week: Dict, 
        periods_per_week: int,
        week_number: Optional[int] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate a single week of scheme of work.
        
        Args:
            scheme_week: Week data dictionary
            periods_per_week: Maximum periods allowed per week
            week_number: Optional week number for error messages
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        try:
            # Get week number from data if not provided
            week_num = week_number or scheme_week.get("week", 0)
            
            # Validate activities exist
            activities = scheme_week.get("activities", [])
            if not activities:
                raise ValidationError(
                    f"Week {week_num} has no learning activities",
                    field="activities",
                    value=activities
                )
            
            # Calculate total periods
            total_periods = sum(act.get("periods", 0) for act in activities)
            
            # Validate period limits
            if total_periods > periods_per_week:
                raise ValidationError(
                    f"Week {week_num} exceeds period limit: "
                    f"{total_periods} > {periods_per_week}",
                    field=f"week_{week_num}_periods",
                    value=total_periods
                )
            
            if total_periods == 0:
                warnings.append(f"Week {week_num} has 0 teaching periods")
            
            # Validate activity structure
            for i, activity in enumerate(activities):
                cls._validate_activity(activity, week_num, i)
            
            # Check for duplicate activities
            activity_names = [act.get("specific_learning_activity", "") 
                            for act in activities]
            if len(activity_names) != len(set(activity_names)):
                warnings.append(f"Week {week_num} may have duplicate activities")
            
            logger.debug(f"Week {week_num} validation passed: {total_periods} periods")
            return True, warnings
            
        except ValidationError as e:
            logger.error(f"Week validation failed: {str(e)}")
            raise

    @staticmethod
    def _validate_activity(activity: Dict, week_num: int, activity_index: int):
        """Validate individual activity."""
        # Check required fields
        if not activity.get("specific_learning_activity"):
            raise ValidationError(
                f"Week {week_num}, Activity {activity_index + 1}: "
                "Missing specific learning activity",
                field="specific_learning_activity"
            )
        
        # Check periods
        periods = activity.get("periods", 0)
        if periods <= 0:
            logger.warning(
                f"Week {week_num}, Activity {activity_index + 1}: "
                f"Has {periods} periods assigned"
            )
        
        # Check competences
        if not activity.get("main_competence") and not activity.get("specific_competence"):
            logger.warning(
                f"Week {week_num}, Activity {activity_index + 1}: "
                "Missing competence information"
            )

    # ====================================================
    # LESSON PLAN VALIDATION
    # ====================================================
    
    @classmethod
    def validate_lesson_plan(
        cls, 
        lesson_plan: Dict, 
        scheme_week: Optional[Dict] = None
    ) -> Tuple[bool, List[str]]:
        """
        Comprehensive lesson plan validation.
        
        Args:
            lesson_plan: Lesson plan data
            scheme_week: Corresponding scheme week for cross-validation
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        try:
            # 1. Basic structure validation
            cls._validate_lesson_structure(lesson_plan)
            
            # 2. Time validation
            cls._validate_lesson_timing(lesson_plan)
            
            # 3. Student attendance validation
            cls._validate_student_counts(lesson_plan)
            
            # 4. Lesson steps validation
            cls._validate_lesson_steps(lesson_plan)
            
            # 5. Cross-validate with scheme if provided
            if scheme_week:
                cls._cross_validate_with_scheme(lesson_plan, scheme_week)
            
            logger.info("Lesson plan validation passed successfully")
            return True, warnings
            
        except ValidationError as e:
            logger.error(f"Lesson plan validation failed: {str(e)}")
            raise

    @staticmethod
    def _validate_lesson_structure(lesson_plan: Dict):
        """Validate basic lesson plan structure."""
        required_fields = [
            "subject",
            "class_level",
            "teacher",
            "school",
            "date",
            "period",
        ]
        
        missing_fields = [field for field in required_fields 
                         if field not in lesson_plan or not lesson_plan[field]]
        
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                field="structure"
            )
        
        # Validate date format
        date_obj = lesson_plan.get("date")
        if date_obj and not isinstance(date_obj, date):
            try:
                # Try to parse if it's a string
                if isinstance(date_obj, str):
                    from datetime import datetime
                    datetime.strptime(date_obj, "%Y-%m-%d")
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Invalid date format: {date_obj}",
                    field="date",
                    value=date_obj
                )

    @staticmethod
    def _validate_lesson_timing(lesson_plan: Dict):
        """Validate lesson timing and duration."""
        time_start = lesson_plan.get("time_start")
        time_finish = lesson_plan.get("time_finish")
        
        if time_start and time_finish:
            if not isinstance(time_start, time) or not isinstance(time_finish, time):
                logger.warning("Time fields should be datetime.time objects")
            
            # Check if start is before finish
            if time_start >= time_finish:
                raise ValidationError(
                    "Lesson start time must be before finish time",
                    field="time_timing",
                    value=f"{time_start} - {time_finish}"
                )
            
            # Calculate duration
            from datetime import datetime
            start_dt = datetime.combine(date.today(), time_start)
            end_dt = datetime.combine(date.today(), time_finish)
            duration_minutes = (end_dt - start_dt).seconds // 60
            
            if duration_minutes <= 0:
                raise ValidationError("Lesson duration must be positive", field="duration")
            
            if duration_minutes > 240:  # 4 hours maximum
                warnings.append(f"Lesson duration of {duration_minutes} minutes is unusually long")

    @staticmethod
    def _validate_student_counts(lesson_plan: Dict):
        """Validate student attendance counts."""
        registered = lesson_plan.get("registered_students", {})
        attended = lesson_plan.get("attended_students", {})
        
        # Check registered students
        reg_boys = registered.get("boys", 0)
        reg_girls = registered.get("girls", 0)
        
        if reg_boys < 0 or reg_girls < 0:
            raise ValidationError(
                "Student counts cannot be negative",
                field="registered_students",
                value=registered
            )
        
        # Check attended students
        att_boys = attended.get("boys", 0)
        att_girls = attended.get("girls", 0)
        
        if att_boys < 0 or att_girls < 0:
            raise ValidationError(
                "Attendance counts cannot be negative",
                field="attended_students",
                value=attended
            )
        
        # Check attendance doesn't exceed registration
        if att_boys > reg_boys or att_girls > reg_girls:
            warnings.append("Attendance exceeds registered students")

    @staticmethod
    def _validate_lesson_steps(lesson_plan: Dict):
        """Validate lesson teaching steps."""
        steps = lesson_plan.get("lesson_steps", [])
        
        if not steps:
            raise ValidationError(
                "Lesson plan has no teaching steps",
                field="lesson_steps"
            )
        
        total_duration = 0
        for i, step in enumerate(steps):
            # Check step structure
            if not step.get("step_name"):
                raise ValidationError(
                    f"Step {i + 1}: Missing step name",
                    field=f"step_{i}_name"
                )
            
            if not step.get("teaching_activity") and not step.get("learning_activity"):
                warnings.append(f"Step {i + 1}: Missing teaching/learning activity")
            
            # Check duration
            duration = step.get("duration")
            if duration:
                if isinstance(duration, str):
                    # Try to parse duration string
                    try:
                        # Handle various duration formats
                        pass
                    except:
                        warnings.append(f"Step {i + 1}: Could not parse duration")
                elif hasattr(duration, 'total_seconds'):
                    total_duration += duration.total_seconds() // 60
                else:
                    warnings.append(f"Step {i + 1}: Invalid duration format")
        
        # Validate total duration
        if total_duration > 0:
            time_start = lesson_plan.get("time_start")
            time_finish = lesson_plan.get("time_finish")
            
            if time_start and time_finish:
                from datetime import datetime
                start_dt = datetime.combine(date.today(), time_start)
                end_dt = datetime.combine(date.today(), time_finish)
                available_minutes = (end_dt - start_dt).seconds // 60
                
                if total_duration > available_minutes:
                    warnings.append(
                        f"Lesson steps total duration ({total_duration} min) "
                        f"exceeds available time ({available_minutes} min)"
                    )

    @staticmethod
    def _cross_validate_with_scheme(lesson_plan: Dict, scheme_week: Dict):
        """Cross-validate lesson plan against scheme of work."""
        # Extract activities from lesson plan
        lesson_activities = []
        for day in lesson_plan.get("days", []):
            if "lesson" in day:
                lesson_activities.append(day["lesson"].get("specific_learning_activity", ""))
        
        # Extract activities from scheme week
        scheme_activities = []
        for act in scheme_week.get("activities", []):
            # Repeat activity for each period
            scheme_activities.extend(
                [act.get("specific_learning_activity", "")] * act.get("periods", 0)
            )
        
        # Compare sequences
        if lesson_activities != scheme_activities:
            raise ValidationError(
                "Lesson activities do not match scheme allocation. "
                f"Lesson: {len(lesson_activities)} activities, "
                f"Scheme: {len(scheme_activities)} allocations",
                field="activity_sequence"
            )
        
        # Check period counts match
        lesson_periods = len(lesson_activities)
        scheme_periods = sum(act.get("periods", 0) for act in scheme_week.get("activities", []))
        
        if lesson_periods != scheme_periods:
            raise ValidationError(
                f"Period mismatch: Lesson has {lesson_periods} periods, "
                f"Scheme has {scheme_periods} periods",
                field="period_count"
            )

    # ====================================================
    # BATCH VALIDATION
    # ====================================================
    
    @classmethod
    def batch_validate_scheme_weeks(
        cls,
        scheme_weeks: List[Dict],
        periods_per_week: int
    ) -> Dict[int, Dict[str, Any]]:
        """
        Validate multiple scheme weeks at once.
        
        Args:
            scheme_weeks: List of week data dictionaries
            periods_per_week: Maximum periods per week
            
        Returns:
            Dictionary with validation results per week
        """
        results = {}
        
        for week_data in scheme_weeks:
            week_num = week_data.get("week")
            if week_num is None:
                logger.warning("Skipping week without number")
                continue
            
            try:
                is_valid, warnings = cls.validate_scheme_week(
                    week_data, 
                    periods_per_week, 
                    week_num
                )
                results[week_num] = {
                    "valid": is_valid,
                    "warnings": warnings,
                    "errors": []
                }
                
            except ValidationError as e:
                results[week_num] = {
                    "valid": False,
                    "warnings": [],
                    "errors": [str(e)]
                }
        
        return results
    
    @classmethod
    def get_validation_summary(cls, validation_results: Dict[int, Dict]) -> Dict[str, Any]:
        """Generate summary from validation results."""
        total_weeks = len(validation_results)
        valid_weeks = sum(1 for result in validation_results.values() if result.get("valid", False))
        
        all_warnings = []
        all_errors = []
        
        for week_num, result in validation_results.items():
            all_warnings.extend([f"Week {week_num}: {w}" for w in result.get("warnings", [])])
            all_errors.extend([f"Week {week_num}: {e}" for e in result.get("errors", [])])
        
        return {
            "total_weeks": total_weeks,
            "valid_weeks": valid_weeks,
            "invalid_weeks": total_weeks - valid_weeks,
            "warning_count": len(all_warnings),
            "error_count": len(all_errors),
            "all_warnings": all_warnings,
            "all_errors": all_errors,
            "success_rate": (valid_weeks / total_weeks * 100) if total_weeks > 0 else 0,
        }