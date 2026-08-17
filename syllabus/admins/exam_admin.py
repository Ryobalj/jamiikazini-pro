# syllabus/admins/exam_admin.py

from django.contrib import admin
from syllabus.models.student import Student
from syllabus.models.exam import Exam
from syllabus.models.mark import Mark


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "class_level", "gender", "workstation", "is_active")
    list_filter = ("class_level", "gender", "is_active")
    search_fields = ("full_name", "admission_number", "workstation__school_name")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("workstation", "class_level")


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "class_level", "term", "year", "workstation", "max_score_per_subject")
    list_filter = ("class_level", "term", "year")
    search_fields = ("name", "workstation__school_name")
    filter_horizontal = ("subjects",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("workstation", "class_level")


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "exam", "score")
    list_filter = ("exam", "subject")
    search_fields = ("student__full_name",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("student", "subject", "exam")
