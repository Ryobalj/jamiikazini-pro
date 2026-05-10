# jamiikazini/syllabus/tests/test_admin/test_specific_competence_admin.py

import pytest
from django.contrib import admin
from syllabus.admins.specific_competence_admin import SpecificCompetenceAdmin
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.main_competence import MainCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel
from syllabus.models.syllabus_version import SyllabusVersion


@pytest.mark.django_db
class TestSpecificCompetenceAdmin:

    @pytest.fixture
    def admin_site(self):
        return admin.site

    @pytest.fixture
    def model_admin(self, admin_site):
        return SpecificCompetenceAdmin(SpecificCompetence, admin_site)

    @pytest.fixture
    def subject(self):
        return Subject.objects.create(name="Science")

    @pytest.fixture
    def class_level(self):
        return ClassLevel.objects.create(name="Grade 5")

    @pytest.fixture
    def syllabus_version(self):
        return SyllabusVersion.objects.create(year=2025)

    @pytest.fixture
    def subject_version(self, subject, class_level, syllabus_version):
        return SubjectVersion.objects.create(
            syllabus_version=syllabus_version,
            subject=subject,
            class_level=class_level
        )

    @pytest.fixture
    def main_competence(self, subject_version):
        return MainCompetence.objects.create(
            subject_version=subject_version,
            name="Main A"
        )

    @pytest.fixture
    def specific_competence(self, main_competence):
        return SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="A Specific Competence for Testing"
        )

    def test_admin_registered(self):
        assert isinstance(
            admin.site._registry.get(SpecificCompetence),
            SpecificCompetenceAdmin
        )

    def test_list_display(self, model_admin):
        assert model_admin.list_display == (
            "name_preview",
            "main_competence",
            "order",
            "created_at",
            "updated_at",
        )

    def test_list_filter(self, model_admin):
        assert model_admin.list_filter == ("main_competence",)

    def test_search_fields(self, model_admin):
        assert model_admin.search_fields == ("name", "main_competence__name")

    def test_ordering(self, model_admin):
        assert model_admin.ordering == ("main_competence", "order")

    def test_readonly_fields(self, model_admin):
        assert model_admin.readonly_fields == ("order", "created_at", "updated_at")

    def test_fieldsets(self, model_admin):
        assert model_admin.fieldsets == (
            ("Specific Competence Info", {
                "fields": ("main_competence", "name", "order")
            }),
            ("Timestamps", {
                "fields": ("created_at", "updated_at")
            }),
        )

    def test_name_preview_shorter(self, model_admin, specific_competence):
        """If text is shorter than 50 chars, no ellipsis."""
        short_name = "Short Text"
        specific_competence.name = short_name
        assert model_admin.name_preview(specific_competence) == short_name

    def test_name_preview_long_text(self, model_admin, specific_competence):
        """If longer than 50 chars, append ..."""
        specific_competence.name = "X" * 60
        result = model_admin.name_preview(specific_competence)
        assert result.startswith("X" * 50)
        assert result.endswith("...")

    def test_name_preview_label(self, model_admin):
        assert model_admin.name_preview.short_description == "Specific Competence"