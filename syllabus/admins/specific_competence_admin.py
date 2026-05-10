# jamiikazini/syllabus/admins/specific_competence_admin.py

import nested_admin
from django.contrib import admin
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.specific_learning_activity import SpecificLearningActivity


class SpecificLearningActivityInline(nested_admin.NestedTabularInline):
    model = SpecificLearningActivity
    extra = 1
    fields = ("name", "leading", "method", "periods")
    show_change_link = True


class LearningActivityInline(nested_admin.NestedTabularInline):
    model = LearningActivity
    extra = 1
    fields = ("name",)
    inlines = [SpecificLearningActivityInline]
    show_change_link = True


@admin.register(SpecificCompetence)
class SpecificCompetenceAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        "name_preview", "main_competence", "order",
        "created_at", "updated_at",
    )
    list_filter = ("main_competence",)
    search_fields = ("name", "main_competence__name")
    ordering = ("main_competence", "order")
    readonly_fields = ("order", "created_at", "updated_at")
    inlines = [LearningActivityInline]

    fieldsets = (
        ("Specific Competence Info", {
            "fields": ("main_competence", "name", "order")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def name_preview(self, obj):
        return obj.name[:50] + ("..." if len(obj.name) > 50 else "")
    name_preview.short_description = "Specific Competence"