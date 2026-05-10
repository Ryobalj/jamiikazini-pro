# syllabus/serializers/scheme_serializers.py

from rest_framework import serializers
from datetime import date

from syllabus.models.subject_version import SubjectVersion
from syllabus.models.annual_calendar import AnnualCalendar
from syllabus.services.data_models import (
    SchemeData,
    ScheduleItem,
    PeriodCalculation,
    SchemeIdentification,
)


# ======================================================
# REQUEST SERIALIZER (USER INPUT)
# ======================================================
class SchemeRequestSerializer(serializers.Serializer):
    subject_version_id = serializers.UUIDField()
    annual_calendar_id = serializers.UUIDField()
    balance_weekly = serializers.BooleanField(default=True)
    language = serializers.ChoiceField(
        choices=[("sw", "Swahili"), ("en", "English")],
        required=False
    )


# ======================================================
# SUPPORTING SERIALIZERS
# ======================================================
class PeriodCalculationSerializer(serializers.Serializer):
    total_periods = serializers.IntegerField()
    periods_per_week = serializers.IntegerField()

    required_weeks = serializers.FloatField()
    available_weeks = serializers.IntegerField()
    available_periods = serializers.IntegerField()

    period_difference = serializers.FloatField()
    distribution_ratio = serializers.FloatField()
    adjusted_periods_per_week = serializers.FloatField()


class CalendarBlockSerializer(serializers.Serializer):
    """
    Serializes CalendarBlock from CalendarService
    """
    block_type = serializers.CharField()  # 'study' | 'break'
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    week_numbers = serializers.ListField(child=serializers.IntegerField())
    duration_days = serializers.IntegerField()
    learning_days = serializers.IntegerField()


class SchemeIdentificationSerializer(serializers.Serializer):
    """
    Serializes SchemeIdentification
    """
    teacher_name = serializers.CharField()
    school_name = serializers.CharField()
    language = serializers.CharField()


class ScheduleItemSerializer(serializers.Serializer):
    week_number = serializers.IntegerField()
    calendar_week = serializers.IntegerField()
    month = serializers.CharField()
    week_date = serializers.DateField(allow_null=True)

    main_competence = serializers.CharField()
    specific_competence = serializers.CharField()

    learning_activity = serializers.CharField()
    student_activity = serializers.CharField()

    periods = serializers.IntegerField()

    methodology = serializers.CharField()
    assessment_criteria = serializers.CharField(allow_null=True, allow_blank=True)
    teaching_aids = serializers.CharField(allow_null=True, allow_blank=True)
    references = serializers.CharField(allow_null=True, allow_blank=True)

    remarks = serializers.CharField(allow_blank=True, allow_null=True)


# ======================================================
# MAIN RESPONSE SERIALIZER (FIXED)
# ======================================================
class SchemeResponseSerializer(serializers.Serializer):
    """
    Serializes SchemeData (DTO) into API response.
    Now includes ALL fields from SchemeData dataclass.
    """

    # Administrative
    council = serializers.CharField()
    ward = serializers.CharField()
    school_name = serializers.CharField()
    teacher_name = serializers.CharField()

    # Academic identifiers
    subject_name = serializers.CharField()
    class_level_name = serializers.CharField()
    year = serializers.CharField()
    term = serializers.CharField()
    term_display = serializers.CharField()

    # Identification
    identification = SchemeIdentificationSerializer()

    # Calendar & periods
    calendar_data = serializers.SerializerMethodField()  # Changed from DictField
    period_calculation = PeriodCalculationSerializer()

    # Scheme meta
    objectives = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True
    )
    
    headers = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True
    )

    # Scheme rows
    schedule_items = ScheduleItemSerializer(many=True)

    def get_calendar_data(self, obj):
        """
        Convert calendar_data (list of CalendarBlock objects) to serializable format.
        """
        if not hasattr(obj, 'calendar_data'):
            return []
        
        calendar_data = obj.calendar_data
        
        # If it's already a list of dicts
        if isinstance(calendar_data, list) and len(calendar_data) > 0:
            if isinstance(calendar_data[0], dict):
                return calendar_data
            
            # If it's a list of CalendarBlock objects
            if hasattr(calendar_data[0], 'block_type'):
                return CalendarBlockSerializer(calendar_data, many=True).data
        
        # If it's a dict
        if isinstance(calendar_data, dict):
            return calendar_data
        
        # Default empty list
        return []

    # Optional: Add computed properties
    total_weeks = serializers.SerializerMethodField()
    total_periods = serializers.SerializerMethodField()
    total_activities = serializers.SerializerMethodField()

    def get_total_weeks(self, obj):
        """Calculate total weeks in the scheme"""
        if hasattr(obj, 'period_calculation') and obj.period_calculation:
            return obj.period_calculation.available_weeks
        return 0

    def get_total_periods(self, obj):
        """Calculate total periods in the scheme"""
        if hasattr(obj, 'period_calculation') and obj.period_calculation:
            return obj.period_calculation.total_periods
        return 0

    def get_total_activities(self, obj):
        """Count total activities/schedule items"""
        if hasattr(obj, 'schedule_items'):
            return len(obj.schedule_items)
        return 0


# ======================================================
# SIMPLIFIED RESPONSE FOR FRONTEND (OPTIONAL)
# ======================================================
class SchemeSimpleResponseSerializer(serializers.Serializer):
    """
    Simplified version for frontend display.
    """
    id = serializers.CharField(source='year')  # Use year as identifier
    subject = serializers.CharField(source='subject_name')
    class_level = serializers.CharField(source='class_level_name')
    year = serializers.CharField()
    teacher = serializers.CharField(source='teacher_name')
    school = serializers.CharField(source='school_name')
    total_weeks = serializers.SerializerMethodField()
    total_periods = serializers.SerializerMethodField()
    generated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M', required=False)

    def get_total_weeks(self, obj):
        if hasattr(obj, 'period_calculation') and obj.period_calculation:
            return obj.period_calculation.available_weeks
        return 0

    def get_total_periods(self, obj):
        if hasattr(obj, 'period_calculation') and obj.period_calculation:
            return obj.period_calculation.total_periods
        return 0


# ======================================================
# PDF REQUEST SERIALIZER (OPTIONAL)
# ======================================================
class SchemePDFRequestSerializer(serializers.Serializer):
    """
    Serializer for PDF generation requests.
    """
    subject_version_id = serializers.PrimaryKeyRelatedField(
        queryset=SubjectVersion.objects.all(),
        source="subject_version"
    )

    annual_calendar_id = serializers.PrimaryKeyRelatedField(
        queryset=AnnualCalendar.objects.all(),
        source="annual_calendar"
    )

    language = serializers.ChoiceField(
        choices=[("sw", "Swahili"), ("en", "English")],
        default="sw",
        required=False
    )

    include_summary = serializers.BooleanField(default=True)
    include_calendar = serializers.BooleanField(default=True)
    watermark = serializers.BooleanField(default=False)
