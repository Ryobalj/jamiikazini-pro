# jamiikazini/syllabus/tests/test_admins/test_teacher_workstation_admin.py

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.admins.teacher_workstation_admin import TeacherWorkStationAdmin


User = get_user_model()


@pytest.mark.django_db
class TestTeacherWorkStationAdmin:

    def setup_method(self):
        self.model_admin = TeacherWorkStationAdmin(TeacherWorkStation, admin.site)

    def test_admin_is_registered(self):
        assert isinstance(admin.site._registry.get(TeacherWorkStation), TeacherWorkStationAdmin)

    def test_list_display(self):
        assert self.model_admin.list_display == (
            "teacher",
            "school_name",
            "district",
            "ward",
            "region",
            "is_active",
            "created_at",
        )

    def test_list_filter(self):
        assert self.model_admin.list_filter == (
            "is_active",
            "district",
            "region",
            "created_at",
        )

    def test_search_fields(self):
        assert self.model_admin.search_fields == (
            "teacher__username",
            "teacher__email",
            "school_name",
            "district",
            "ward",
            "region",
        )

    def test_autocomplete_fields(self):
        assert self.model_admin.autocomplete_fields == ("teacher",)

    def test_readonly_fields(self):
        assert self.model_admin.readonly_fields == (
            "id",
            "created_at",
            "updated_at",
        )

    def test_fieldsets(self):
        assert self.model_admin.fieldsets == (
            ("Taarifa za Mwl na Kituo", {
                "fields": (
                    "teacher",
                    "school_name",
                    "district",
                    ("ward", "region"),
                )
            }),
            ("Hali ya Kazi", {
                "fields": ("is_active",)
            }),
            ("Taarifa za Mfumo", {
                "classes": ("collapse",),
                "fields": ("id", "created_at", "updated_at"),
            }),
        )