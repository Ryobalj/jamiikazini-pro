# syllabus/admins/time_table_admin.py

from django.contrib import admin
from syllabus.models.timetable import TimeTable


@admin.register(TimeTable)
class TimeTableAdmin(admin.ModelAdmin):
    list_display = (
        "workstation_display",
        "subject_display",
        "period",
        "timestart",
        "timefinish",
        "registeredboys",
        "registeredgirls",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "period",
        "workstation__district",
        "workstation__region",
        "subject_version__class_level",
        "subject_version__syllabus_version__year",
    )
    search_fields = (
        "workstation__teacher__username",
        "workstation__teacher__email",
        "workstation__school_name",
        "subject_version__subject__name",
        "subject_version__class_level__name",
    )
    ordering = ("workstation", "period")

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Teacher Workstation", {
            "fields": ("workstation",)
        }),
        ("Subject & Lesson Details", {
            "fields": (
                "subject_version",
                "period",
                "timestart",
                "timefinish",
            )
        }),
        ("Class Registration", {
            "fields": (
                "registeredboys",
                "registeredgirls",
            )
        }),
        ("Status", {
            "fields": ("status",)
        }),
        ("Metadata", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )

    # -------------------------
    # Custom display fields
    # -------------------------
    def workstation_display(self, obj):
        return f"{obj.workstation.teacher.username} — {obj.workstation.school_name}"
    workstation_display.short_description = "Workstation"

    def subject_display(self, obj):
        sv = obj.subject_version
        return f"{sv.subject.name} ({sv.class_level.name})"
    subject_display.short_description = "Subject"

    # -------------------------
    # Query optimization
    # -------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "workstation",
            "workstation__teacher",
            "subject_version",
            "subject_version__subject",
            "subject_version__class_level",
        )