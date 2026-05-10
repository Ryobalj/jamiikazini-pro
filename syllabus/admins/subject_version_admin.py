# jamiikazini/syllabus/admins/subject_version_admin.py

import nested_admin
from django.contrib import admin
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.main_competence import MainCompetence
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.specific_learning_activity import SpecificLearningActivity


class SpecificLearningActivityInline(nested_admin.NestedTabularInline):
    model = SpecificLearningActivity
    extra = 1
    fields = ("name", "leading", "method", "periods", "assessment_criteria", "teaching_aids", "references")
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


class MainCompetenceInline(nested_admin.NestedTabularInline):
    model = MainCompetence
    extra = 1
    fields = ("name",)
    inlines = [SpecificCompetenceInline]
    show_change_link = True


@admin.register(SubjectVersion)
class SubjectVersionAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        "subject", "class_level", "syllabus_version",
        "is_english", "is_awali", "order", "created_at",
    )
    list_filter = ("syllabus_version", "class_level", "is_english", "is_awali")
    search_fields = ("subject__name", "class_level__name", "syllabus_version__year")
    autocomplete_fields = ("subject", "class_level", "syllabus_version")
    readonly_fields = ("order", "created_at", "updated_at")
    inlines = [MainCompetenceInline]

    fieldsets = (
        ("Core Information", {
            "fields": ("syllabus_version", "subject", "class_level")
        }),
        ("Curriculum Flags", {
            "fields": ("is_english", "is_awali"),
        }),
        ("System Metadata", {
            "classes": ("collapse",),
            "fields": ("order", "created_at", "updated_at"),
        }),
    )
    ordering = ("syllabus_version", "class_level", "order")