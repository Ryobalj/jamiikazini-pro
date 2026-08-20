# syllabus/serializers/master_timetable_serializers.py
from django.db.models import Q
from rest_framework import serializers

from syllabus.models.master_timetable import (
    MasterTimetableRoster,
    TimetablePeriodSlot,
    ActivityType,
    TimetableTeacher,
    TimetableTeacherAssignment,
    TimetableSlot,
)


class MasterTimetableRosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterTimetableRoster
        fields = ["id", "name", "year", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class TimetablePeriodSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimetablePeriodSlot
        fields = ["id", "roster", "order", "label", "timestart", "timefinish", "is_break"]
        read_only_fields = ["id"]


class ActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityType
        fields = [
            "id", "code", "label_sw", "label_en",
            "is_fixed_routine", "is_whole_school", "default_order",
        ]
        read_only_fields = ["id"]


class TimetableTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimetableTeacher
        fields = ["id", "roster", "full_name", "initials", "workstation"]
        read_only_fields = ["id"]

    def validate(self, data):
        roster = data.get("roster", getattr(self.instance, "roster", None))
        initials = data.get("initials", getattr(self.instance, "initials", None))
        if roster and initials:
            clash = TimetableTeacher.objects.filter(roster=roster, initials__iexact=initials)
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                suggestion = self._suggest_initials(roster, initials)
                raise serializers.ValidationError({
                    "initials": (
                        f"Herufi '{initials}' tayari zinatumika na mwalimu mwingine kwenye roster "
                        f"hii. Kila mwalimu anatambulika kwenye ratiba kwa herufi zake pekee, hivyo "
                        f"lazima ziwe za kipekee. Jaribu '{suggestion}'."
                    )
                })
        return data

    @staticmethod
    def _suggest_initials(roster, initials):
        existing = set(
            TimetableTeacher.objects.filter(roster=roster).values_list("initials", flat=True)
        )
        for n in range(2, 20):
            candidate = f"{initials}{n}"
            if candidate not in existing:
                return candidate
        return initials


class TimetableTeacherAssignmentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    teacher_initials = serializers.CharField(source="teacher.initials", read_only=True)
    subject_name = serializers.CharField(source="subject_version.subject.name", read_only=True)
    class_level_name = serializers.CharField(source="subject_version.class_level.name", read_only=True)
    nominal_periods_per_week = serializers.IntegerField(
        source="subject_version.subject.periods_per_week", read_only=True
    )
    effective_periods_per_week = serializers.IntegerField(read_only=True)

    class Meta:
        model = TimetableTeacherAssignment
        fields = [
            "id", "roster", "teacher", "teacher_name", "teacher_initials",
            "subject_version", "subject_name", "class_level_name",
            "nominal_periods_per_week", "periods_per_week_override",
            "effective_periods_per_week",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        teacher = data.get("teacher", getattr(self.instance, "teacher", None))
        subject_version = data.get("subject_version", getattr(self.instance, "subject_version", None))
        if teacher and subject_version:
            clash = TimetableTeacherAssignment.objects.filter(
                teacher=teacher, subject_version=subject_version
            )
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError(
                    "Mwalimu huyu tayari amegawiwa somo hili kwa darasa hili."
                )
        return data


class TimetableSlotSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)
    class_level_name = serializers.CharField(source="class_level.name", read_only=True, default=None)
    teacher_initials = serializers.CharField(source="assignment.teacher.initials", read_only=True, default=None)
    subject_name = serializers.CharField(source="assignment.subject_version.subject.name", read_only=True, default=None)
    activity_label = serializers.CharField(source="activity_type.label_sw", read_only=True, default=None)

    class Meta:
        model = TimetableSlot
        fields = [
            "id", "roster", "day_of_week", "day_of_week_display", "period_slot",
            "class_level", "class_level_name", "assignment", "teacher_initials",
            "subject_name", "activity_type", "activity_label", "custom_label", "source",
        ]
        read_only_fields = ["id", "source"]

    def validate(self, data):
        roster = data.get("roster", getattr(self.instance, "roster", None))
        day_of_week = data.get("day_of_week", getattr(self.instance, "day_of_week", None))
        period_slot = data.get("period_slot", getattr(self.instance, "period_slot", None))
        class_level = data.get("class_level", getattr(self.instance, "class_level", None))
        assignment = data.get("assignment", getattr(self.instance, "assignment", None))
        activity_type = data.get("activity_type", getattr(self.instance, "activity_type", None))
        custom_label = data.get("custom_label", getattr(self.instance, "custom_label", ""))

        if not (assignment or activity_type or custom_label):
            raise serializers.ValidationError(
                "Weka somo (assignment), aina ya shughuli, au jina maalum."
            )

        if roster and day_of_week and period_slot:
            # Same class/day/period can't be filled twice. A whole-school
            # row (class_level=None) blocks every class for that
            # day/period, and placing a class-specific row when a
            # whole-school row already occupies that slot is also a
            # clash - check both directions with one OR.
            clash = TimetableSlot.objects.filter(
                roster=roster, day_of_week=day_of_week, period_slot=period_slot,
            ).filter(Q(class_level=class_level) | Q(class_level__isnull=True))
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError(
                    "Nafasi hii ya kipindi tayari imejazwa kwa darasa hili (au shughuli ya shule nzima)."
                )

        if assignment and day_of_week and period_slot:
            teacher_clash = TimetableSlot.objects.filter(
                roster=roster, day_of_week=day_of_week, period_slot=period_slot,
                assignment__teacher=assignment.teacher,
            )
            if self.instance:
                teacher_clash = teacher_clash.exclude(pk=self.instance.pk)
            if teacher_clash.exists():
                raise serializers.ValidationError(
                    f"Mwalimu {assignment.teacher.initials} tayari ana kipindi kingine wakati huu."
                )

        return data
