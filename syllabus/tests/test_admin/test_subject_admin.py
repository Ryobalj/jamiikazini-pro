# jamiikazini/syllabus/tests/test_admin/test_subject_admin.py

import pytest
from django.contrib.admin.sites import AdminSite
from syllabus.admins.subject_admin import SubjectAdmin
from syllabus.models.subject import Subject


@pytest.mark.django_db
class TestSubjectAdmin:
    def setup_method(self):
        self.site = AdminSite()
        self.admin = SubjectAdmin(Subject, self.site)

    def test_list_display(self):
        assert self.admin.list_display == ("name", "code", "periods_per_week", "description", "created_at")

    def test_search_fields(self):
        assert self.admin.search_fields == ("name", "code")

    def test_list_filter(self):
        assert self.admin.list_filter == ("created_at", "periods_per_week")

    def test_ordering(self):
        assert self.admin.ordering == ("name",)

    def test_readonly_fields(self):
        assert self.admin.readonly_fields == ("code", "created_at", "updated_at")

    def test_fieldsets_structure(self):
        assert self.admin.fieldsets == (
            (
                "Basic Information",
                {
                    "fields": ("name", "description", "periods_per_week"),
                    "description": "Hapa unaweza kuweka idadi ya vipindi kwa wiki kwa kila somo.",
                }
            ),
            (
                "System Generated",
                {
                    "classes": ("collapse",),
                    "fields": ("code", "created_at", "updated_at")
                },
            ),
        )