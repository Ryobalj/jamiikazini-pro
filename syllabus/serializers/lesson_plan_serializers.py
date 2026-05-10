# syllabus/serializers/lesson_plan_serializers.py
from rest_framework import serializers
from datetime import timedelta

from syllabus.models.timetable import TimeTable
from syllabus.models.specific_learning_activity import SpecificLearningActivity
from syllabus.services.academic_context import AcademicContext


class LessonPlanRequestSerializer(serializers.Serializer):
    """
    Serializer for Auto Lesson Plan user input (DTO, not ModelSerializer)
    """

    # --------------------
    # REQUIRED REFERENCES
    # --------------------
    timetable = serializers.PrimaryKeyRelatedField(
        queryset=TimeTable.objects.select_related(
            "subject_version",
            "workstation"
        ).all()
    )

    specific_activity = serializers.PrimaryKeyRelatedField(
        queryset=SpecificLearningActivity.objects.select_related(
            "learning_activity__specific_competence__main_competence__subject_version"
        ).all()
    )

    # --------------------
    # CORE LESSON INFO
    # --------------------
    date = serializers.DateField()

    # UI has priority; if null → timetable used in AcademicContext
    period = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True
    )

    timestart = serializers.TimeField(
        required=False,
        allow_null=True
    )

    timefinish = serializers.TimeField(
        required=False,
        allow_null=True
    )

    # --------------------
    # ATTENDANCE
    # --------------------
    boys_attended = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0
    )

    girls_attended = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0
    )

    # --------------------
    # OPTIONS
    # --------------------
    language = serializers.ChoiceField(
        choices=[("sw", "Swahili"), ("en", "English")],
        required=False
    )

    is_song = serializers.BooleanField(default=False)
    repeat_next = serializers.BooleanField(default=False)

    managed_count = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0
    )

    # --------------------
    # VALIDATION
    # --------------------
    def validate(self, data):
        timetable = data["timetable"]
        activity = data["specific_activity"]

        subject_version = timetable.subject_version

        # 🔗 Ensure SpecificLearningActivity belongs to same SubjectVersion
        activity_sv = (
            activity.learning_activity
            .specific_competence
            .main_competence
            .subject_version
        )

        if activity_sv != subject_version:
            raise serializers.ValidationError(
                {
                    "specific_activity": (
                        "Selected activity does not belong to the timetable subject."
                    )
                }
            )

        # ⏱️ Logical time validation (if both provided)
        timestart = data.get("timestart")
        timefinish = data.get("timefinish")

        if timestart and timefinish and timestart >= timefinish:
            raise serializers.ValidationError(
                {
                    "timefinish": (
                        "timefinish must be later than timestart."
                    )
                }
            )

        return data


# ====================================================
# SERIALIZERS FOR LessonPlanData STRUCTURE
# ====================================================

class LessonPlanMetaSerializer(serializers.Serializer):
    subject = serializers.CharField()
    class_level = serializers.CharField()
    teacher = serializers.CharField()
    school = serializers.CharField()
    date = serializers.DateField()
    period = serializers.IntegerField()
    timestart = serializers.TimeField()
    timefinish = serializers.TimeField()


class LessonPlanIdentificationSerializer(serializers.Serializer):
    school_name = serializers.CharField()
    teacher_name = serializers.CharField()
    main_competence = serializers.CharField()
    class_level = serializers.CharField()
    period = serializers.IntegerField()
    date = serializers.DateField()
    time_start = serializers.TimeField()
    time_finish = serializers.TimeField()
    language = serializers.CharField()
    
    # Computed field
    duration = serializers.SerializerMethodField()
    
    def get_duration(self, obj):
        """Calculate duration in minutes"""
        if not obj.time_start or not obj.time_finish:
            return ""
        
        from datetime import datetime
        start_dt = datetime.combine(obj.date, obj.time_start)
        end_dt = datetime.combine(obj.date, obj.time_finish)
        
        if end_dt <= start_dt:
            return ""
        
        delta = end_dt - start_dt
        minutes = int(delta.total_seconds() // 60)
        return f"{minutes} min"


class LessonPlanSubjectInfoSerializer(serializers.Serializer):
    specific_competence = serializers.CharField()
    main_activity = serializers.CharField()
    specific_activity = serializers.CharField()
    teaching_aids = serializers.CharField()
    references = serializers.CharField()


class StudentCountSerializer(serializers.Serializer):
    boys = serializers.IntegerField()
    girls = serializers.IntegerField()
    total = serializers.SerializerMethodField()
    
    def get_total(self, obj):
        return obj.boys + obj.girls


class LessonStepSerializer(serializers.Serializer):
    step_name = serializers.CharField()
    duration = serializers.DurationField()
    teaching_activity = serializers.CharField()
    learning_activity = serializers.CharField()
    assessment_indicator = serializers.CharField()
    
    # For backward compatibility with old frontend
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()
    
    def get_title(self, obj):
        return obj.step_name
    
    def get_description(self, obj):
        return f"{obj.teaching_activity}\n\n{obj.learning_activity}"
    
    def get_duration_minutes(self, obj):
        return int(obj.duration.total_seconds() // 60)
    
    def get_activities(self, obj):
        return [obj.teaching_activity, obj.learning_activity]


class LessonReflectionSerializer(serializers.Serializer):
    teaching_comment = serializers.CharField(allow_blank=True, required=False)
    assessment_comment = serializers.CharField(allow_blank=True, required=False)
    next_plan_comment = serializers.CharField(allow_blank=True, required=False)


class LessonAssessmentSerializer(serializers.Serializer):
    criteria = serializers.CharField()
    tools = serializers.CharField(required=False)
    remarks = serializers.CharField(required=False)


# ====================================================
# MAIN RESPONSE SERIALIZER (FIXED VERSION)
# ====================================================

class LessonPlanResponseSerializer(serializers.Serializer):
    """
    Production-ready serializer for LessonPlanData.
    Now properly handles meta field and provides backward compatibility.
    """
    
    # 🔴 FIXED: META FIELD IS NOW PRESENT IN LessonPlanData
    meta = LessonPlanMetaSerializer()
    
    # Core fields (matches LessonPlanData)
    identification = LessonPlanIdentificationSerializer()
    registered_students = StudentCountSerializer()
    attended_students = StudentCountSerializer()
    subject_info = LessonPlanSubjectInfoSerializer()
    lesson_steps = LessonStepSerializer(many=True)
    reflection = LessonReflectionSerializer(required=False, allow_null=True)
    
    # Computed convenience fields
    total_registered = serializers.SerializerMethodField()
    total_attended = serializers.SerializerMethodField()
    total_duration_minutes = serializers.SerializerMethodField()
    
    # Backward compatibility fields (for old frontend)
    lesson = serializers.SerializerMethodField()
    steps = serializers.SerializerMethodField()
    assessment = serializers.SerializerMethodField()
    
    def get_total_registered(self, obj):
        return obj.total_registered
    
    def get_total_attended(self, obj):
        return obj.total_attended
    
    def get_total_duration_minutes(self, obj):
        return obj.total_duration_minutes
    
    # Backward compatibility methods
    def get_lesson(self, obj):
        """Create lesson object for old frontend compatibility"""
        return {
            "title": f"{obj.identification.main_competence} - {obj.subject_info.specific_competence}",
            "description": obj.subject_info.main_activity,
            "date": obj.identification.date,
            "period": obj.identification.period,
            "duration": obj.identification.duration,
            "language": obj.identification.language,
            "specific_activity": obj.subject_info.specific_activity,
            "teaching_aids": obj.subject_info.teaching_aids,
            "references": obj.subject_info.references,
        }
    
    def get_steps(self, obj):
        """Create steps array in old format for backward compatibility"""
        return LessonStepSerializer(many=True).to_representation(obj.lesson_steps)
    
    def get_assessment(self, obj):
        """Create assessment object if reflection exists"""
        if not obj.reflection:
            return None
        
        return {
            "criteria": "Lesson Reflection and Assessment",
            "tools": "Teacher observation, student participation, and assessment indicators",
            "remarks": (
                f"Teaching Comment: {obj.reflection.teaching_comment or 'N/A'}\n"
                f"Assessment Comment: {obj.reflection.assessment_comment or 'N/A'}\n"
                f"Next Plan: {obj.reflection.next_plan_comment or 'N/A'}"
            )
        }