# syllabus/admins/main_competence_admin.py

import nested_admin
from django.contrib import admin
from syllabus.models.main_competence import MainCompetence
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


class SpecificCompetenceInline(nested_admin.NestedTabularInline):
    model = SpecificCompetence
    extra = 1
    fields = ("name",)
    inlines = [LearningActivityInline]
    show_change_link = True


@admin.register(MainCompetence)
class MainCompetenceAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name_preview", "subject_version", "order", "created_at", "updated_at")
    list_filter = ("subject_version",)
    search_fields = ("name", "subject_version__subject__name")
    ordering = ("subject_version", "order")
    readonly_fields = ("order", "created_at", "updated_at")
    inlines = [SpecificCompetenceInline]

    fieldsets = (
        ("General Info", {
            "fields": ("subject_version", "name", "order")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def name_preview(self, obj):
        return obj.name[:50] + ("..." if len(obj.name) > 50 else "")
    name_preview.short_description = "Name"