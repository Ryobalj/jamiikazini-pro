# jamiikazini/syllabus/tests/test_admin/test_syllabus_version_admin.py

import pytest
from django.contrib.admin.sites import AdminSite
from syllabus.admins.syllabus_version_admin import SyllabusVersionAdmin
from syllabus.models.syllabus_version import SyllabusVersion


@pytest.mark.django_db
class TestSyllabusVersionAdmin:

    @pytest.fixture
    def admin_instance(self):
        return SyllabusVersionAdmin(SyllabusVersion, AdminSite())

    def test_list_display(self, admin_instance):
        assert admin_instance.list_display == (
            "year",
            "is_current",
            "short_evaluation_aid",
            "created_at",
            "updated_at",
        )

    def test_list_filter(self, admin_instance):
        assert admin_instance.list_filter == ("is_current", "created_at")

    def test_search_fields(self, admin_instance):
        assert admin_instance.search_fields == ("year",)

    def test_ordering(self, admin_instance):
        assert admin_instance.ordering == ("-year",)

    def test_readonly_fields(self, admin_instance):
        assert admin_instance.readonly_fields == ("created_at", "updated_at")

    def test_fieldsets(self, admin_instance):
        fieldsets = admin_instance.fieldsets

        assert fieldsets[0][0] == "Syllabus Version Details"
        assert fieldsets[0][1]["fields"] == (
            "year",
            "evaluation_aid",
            "is_current",
        )

        assert fieldsets[1][0] == "System Metadata"
        assert fieldsets[1][1]["fields"] == ("created_at", "updated_at")

    def test_short_evaluation_aid_empty(self, admin_instance):
        obj = SyllabusVersion(year=2024, evaluation_aid="")
        assert admin_instance.short_evaluation_aid(obj) == "—"

    def test_short_evaluation_aid_short_text(self, admin_instance):
        obj = SyllabusVersion(
            year=2024,
            evaluation_aid="Short evaluation text"
        )
        assert admin_instance.short_evaluation_aid(obj) == "Short evaluation text"

    def test_short_evaluation_aid_truncated(self, admin_instance):
        obj = SyllabusVersion(
            year=2024,
            evaluation_aid="x" * 80  # long text
        )
        result = admin_instance.short_evaluation_aid(obj)

        assert result.startswith("x" * 50)
        assert result.endswith("...")
        assert len(result) == 53  # 50 chars + "..."