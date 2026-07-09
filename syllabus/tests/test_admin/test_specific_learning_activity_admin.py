# jamiikazini/syllabus/tests/test_admin/test_specific_learning_activity_admin.py

import pytest
from django.contrib.admin.sites import AdminSite
from syllabus.admins.specific_learning_activity_admin import SpecificLearningActivityAdmin
from syllabus.models.specific_learning_activity import SpecificLearningActivity
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.main_competence import MainCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.class_level import ClassLevel
from syllabus.models.subject import Subject

@pytest.mark.django_db
class TestSpecificLearningActivityAdmin:

    @pytest.fixture
    def site(self):
        return AdminSite()

    @pytest.fixture
    def syllabus_version(self):
        return SyllabusVersion.objects.create(year=2025)

    @pytest.fixture
    def class_level(self):
        return ClassLevel.objects.create(name="Form 1")

    @pytest.fixture
    def subject(self):
        return Subject.objects.create(name="Mathematics")

    @pytest.fixture
    def subject_version(self, syllabus_version, subject, class_level):
        return SubjectVersion.objects.create(
            syllabus_version=syllabus_version,
            subject=subject,
            class_level=class_level
        )

    @pytest.fixture
    def main_competence(self, subject_version):
        return MainCompetence.objects.create(
            subject_version=subject_version,
            name="Main Competence A"
        )

    @pytest.fixture
    def specific_competence(self, main_competence):
        return SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="Specific Competence A"
        )

    @pytest.fixture
    def learning_activity(self, specific_competence):
        return LearningActivity.objects.create(
            specific_competence=specific_competence,
            name="Test Learning Activity"
        )

    @pytest.fixture
    def admin_instance(self, site):
        return SpecificLearningActivityAdmin(SpecificLearningActivity, site)

    def test_list_display(self, admin_instance, learning_activity):
        obj = SpecificLearningActivity.objects.create(
            learning_activity=learning_activity,
            method="Some teaching method",
            name="Activity Name",
            assessment_criteria="Criteria",
            teaching_aids=["Aids"],
        )
        list_display = admin_instance.get_list_display(request=None)
        assert "name_preview" in list_display
        assert "learning_activity" in list_display
        assert "method_preview" in list_display
        assert "periods" in list_display
        assert "order" in list_display

        # test custom preview methods
        assert admin_instance.name_preview(obj) == "Activity Name"
        assert admin_instance.method_preview(obj) == "Some teaching method"

    def test_method_preview_truncation(self, admin_instance, learning_activity):
        long_method = "M" * 50
        obj = SpecificLearningActivity.objects.create(
            learning_activity=learning_activity,
            method=long_method,
            name="Activity Name",
            assessment_criteria="Criteria",
            teaching_aids=["Aids"],
        )
        preview = admin_instance.method_preview(obj)
        assert len(preview) <= 43  # 40 chars + "..."
        assert preview.endswith("...")

    def test_name_preview_truncation(self, admin_instance, learning_activity):
        long_name = "N" * 60
        obj = SpecificLearningActivity.objects.create(
            learning_activity=learning_activity,
            method="Method",
            name=long_name,
            assessment_criteria="Criteria",
            teaching_aids=["Aids"],
        )
        preview = admin_instance.name_preview(obj)
        assert len(preview) <= 53  # 50 chars + "..."
        assert preview.endswith("...")

    def test_readonly_fields(self, admin_instance):
        readonly = admin_instance.get_readonly_fields(request=None, obj=None)
        assert "order" in readonly
        assert "created_at" in readonly
        assert "updated_at" in readonly