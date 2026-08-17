# jamiikazini/syllabus/admins/specific_learning_activity_admin.py

from django.contrib import admin
from syllabus.models.specific_learning_activity import SpecificLearningActivity


@admin.register(SpecificLearningActivity)
class SpecificLearningActivityAdmin(admin.ModelAdmin):
    list_display = (
        "leading_preview",
        "name_preview",
        "learning_activity",
        "method_preview",
        "periods",
        "order",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "learning_activity__specific_competence__main_competence__subject_version__class_level",
        "learning_activity__specific_competence__main_competence__subject_version__subject",
        "learning_activity",
    )

    search_fields = (
        "leading",
        "name",
        "learning_activity__name",
        "method",
        "assessment_criteria",
    )

    ordering = ("learning_activity", "order")

    readonly_fields = ("order", "created_at", "updated_at")

    fieldsets = (
        ("Parent Activity", {
            "fields": ("learning_activity", "order")
        }),
        ("Descriptions", {
            "fields": (
                "leading",
                "name",
                "method",
                "assessment_criteria",
                "teaching_aids",
                "references",
            )
        }),
        ("Time Allocation", {
            "fields": ("periods",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    # ============================
    # PREVIEW METHODS
    # ============================

    def leading_preview(self, obj):
        if not obj.leading:
            return "-"
        text = ", ".join(obj.leading)
        return text[:40] + ("..." if len(text) > 40 else "")
    leading_preview.short_description = "Leading"

    def name_preview(self, obj):
        return obj.name[:50] + ("..." if len(obj.name) > 50 else "")
    name_preview.short_description = "Specific Activity"

    def method_preview(self, obj):
        if not obj.method:
            return "-"
        return obj.method[:40] + ("..." if len(obj.method) > 40 else "")
    method_preview.short_description = "Method"