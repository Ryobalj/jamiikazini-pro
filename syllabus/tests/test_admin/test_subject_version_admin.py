# jamiikazini/syllabus/tests/test_admin/test_subject_version_admin.py

import pytest
from django.contrib.admin.sites import AdminSite
from syllabus.admins.subject_version_admin import SubjectVersionAdmin
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.subject import Subject
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.class_level import ClassLevel


@pytest.mark.django_db
class TestSubjectVersionAdmin:

    def setup_method(self):
        self.site = AdminSite()

        self.admin = SubjectVersionAdmin(
            model=SubjectVersion,
            admin_site=self.site
        )

        self.syllabus_version = SyllabusVersion.objects.create(year=2024)
        self.subject = Subject.objects.create(name="Mathematics")
        self.level = ClassLevel.objects.create(name="P1", order=1)

        self.instance = SubjectVersion.objects.create(
            syllabus_version=self.syllabus_version,
            subject=self.subject,
            class_level=self.level,
            is_english=True,
            is_awali=False
        )

    def test_list_display(self):
        assert self.admin.list_display == (
            "subject",
            "class_level",
            "syllabus_version",
            "is_english",
            "is_awali",
            "order",
            "created_at",
        )

    def test_list_filter(self):
        assert self.admin.list_filter == (
            "syllabus_version",
            "class_level",
            "is_english",
            "is_awali",
            "created_at",
        )

    def test_search_fields(self):
        assert self.admin.search_fields == (
            "subject__name",
            "class_level__name",
            "syllabus_version__year",
        )

    def test_autocomplete_fields(self):
        assert self.admin.autocomplete_fields == (
            "subject",
            "class_level",
            "syllabus_version",
        )

    def test_readonly_fields(self):
        assert self.admin.readonly_fields == (
            "order",
            "created_at",
            "updated_at",
        )

    def test_ordering(self):
        assert self.admin.ordering == (
            "syllabus_version",
            "class_level",
            "order",
        )

    def test_fieldsets_structure(self):
        """
        Validate fieldsets shape & field grouping.
        """
        fieldsets = self.admin.fieldsets

        assert fieldsets[0][0] == "Core Information"
        assert fieldsets[0][1]["fields"] == (
            "syllabus_version",
            "subject",
            "class_level",
        )

        assert fieldsets[1][0] == "Curriculum Flags"
        assert fieldsets[1][1]["fields"] == ("is_english", "is_awali")

        assert fieldsets[2][0] == "System Metadata"
        assert "collapse" in fieldsets[2][1]["classes"]
        assert fieldsets[2][1]["fields"] == (
            "order",
            "created_at",
            "updated_at",
        )