# syllabus/admins/master_timetable_admin.py

from django.contrib import admin
from syllabus.models.master_timetable import (
    MasterTimetableRoster,
    TimetablePeriodSlot,
    ActivityType,
    TimetableTeacher,
    TimetableTeacherAssignment,
    TimetableSlot,
)


@admin.register(MasterTimetableRoster)
class MasterTimetableRosterAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "owner_display", "is_active", "created_at")
    list_filter = ("year", "is_active")
    search_fields = ("name", "owner__school_name", "owner__teacher__email")

    def owner_display(self, obj):
        return f"{obj.owner.teacher.username} — {obj.owner.school_name}"
    owner_display.short_description = "Owner"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("owner", "owner__teacher")


@admin.register(TimetablePeriodSlot)
class TimetablePeriodSlotAdmin(admin.ModelAdmin):
    list_display = ("roster", "order", "label", "is_break", "timestart", "timefinish")
    list_filter = ("is_break",)
    ordering = ("roster", "order")


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "label_sw", "label_en", "is_fixed_routine", "is_whole_school", "default_order")
    list_filter = ("is_fixed_routine", "is_whole_school")
    search_fields = ("code", "label_sw", "label_en")
    ordering = ("default_order", "code")


@admin.register(TimetableTeacher)
class TimetableTeacherAdmin(admin.ModelAdmin):
    list_display = ("full_name", "initials", "roster", "workstation")
    search_fields = ("full_name", "initials", "roster__name")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("roster", "workstation")


@admin.register(TimetableTeacherAssignment)
class TimetableTeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ("teacher", "subject_display", "effective_periods_per_week", "roster")
    search_fields = ("teacher__full_name", "teacher__initials", "subject_version__subject__name")

    def subject_display(self, obj):
        sv = obj.subject_version
        return f"{sv.subject.name} ({sv.class_level.name})"
    subject_display.short_description = "Subject (Class)"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "roster", "teacher", "subject_version", "subject_version__subject", "subject_version__class_level",
        )


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ("roster", "get_day_of_week_display_", "period_slot", "class_level_display", "what_display", "source")
    list_filter = ("day_of_week", "source")
    ordering = ("roster", "day_of_week", "period_slot__order")

    def get_day_of_week_display_(self, obj):
        return obj.get_day_of_week_display()
    get_day_of_week_display_.short_description = "Day"

    def class_level_display(self, obj):
        return obj.class_level.name if obj.class_level else "Shule Nzima"
    class_level_display.short_description = "Class"

    def what_display(self, obj):
        if obj.assignment:
            return f"{obj.assignment.subject_version.subject.name} ({obj.assignment.teacher.initials})"
        if obj.activity_type:
            return obj.activity_type.label_sw
        return obj.custom_label
    what_display.short_description = "What"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "roster", "period_slot", "class_level", "activity_type",
            "assignment", "assignment__teacher", "assignment__subject_version",
            "assignment__subject_version__subject",
        )
