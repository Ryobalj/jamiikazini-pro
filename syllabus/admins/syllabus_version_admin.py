# jamiikazini/syllabus/admins/syllabus_version_admin.py

from django.contrib import admin
from syllabus.models.syllabus_version import SyllabusVersion


@admin.register(SyllabusVersion)
class SyllabusVersionAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "is_current",
        "short_evaluation_aid",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_current", "created_at")
    search_fields = ("year",)
    ordering = ("-year",)

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Syllabus Version Details", {
            "fields": (
                "year",
                "evaluation_aid",
                "is_current",
            )
        }),
        ("System Metadata", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )

    def short_evaluation_aid(self, obj):
        if not obj.evaluation_aid:
            return "—"
        text = obj.evaluation_aid.strip()
        return text[:50] + ("..." if len(text) > 50 else "")
    short_evaluation_aid.short_description = "Evaluation Aid"