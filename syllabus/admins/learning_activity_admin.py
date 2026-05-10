# jamiikazini/syllabus/admins/learning_activity_admin.py

import nested_admin
from django.contrib import admin
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.specific_learning_activity import SpecificLearningActivity


class SpecificLearningActivityInline(nested_admin.NestedTabularInline):
    model = SpecificLearningActivity
    extra = 1
    fields = ("name", "leading", "method", "periods", "assessment_criteria", "teaching_aids", "references")
    show_change_link = True


@admin.register(LearningActivity)
class LearningActivityAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        "name", "specific_competence", "order",
        "created_at", "updated_at",
    )
    list_filter = ("specific_competence",)
    search_fields = ("name", "specific_competence__name")
    ordering = ("specific_competence", "order")
    readonly_fields = ("order", "created_at", "updated_at")
    autocomplete_fields = ("specific_competence",)
    inlines = [SpecificLearningActivityInline]