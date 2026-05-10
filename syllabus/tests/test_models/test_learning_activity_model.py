# syllabus/tests/test_models/test_learning_activity_model.py

import pytest
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.main_competence import MainCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel
from syllabus.models.syllabus_version import SyllabusVersion

@pytest.mark.django_db
class TestLearningActivityModel:

    @pytest.fixture
    def syllabus_version(self):
        return SyllabusVersion.objects.create(year=2025)

    @pytest.fixture
    def subject_version(self, syllabus_version):
        subject = Subject.objects.create(name="Mathematics")
        class_level = ClassLevel.objects.create(name="P1", order=1)
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
    def competence(self, main_competence):
        return SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="Math Competence"
        )

    def test_auto_order_on_create(self, competence):
        activity1 = LearningActivity.objects.create(
            specific_competence=competence,
            name="Addition"
        )
        activity2 = LearningActivity.objects.create(
            specific_competence=competence,
            name="Subtraction"
        )
        assert activity1.order == 1
        assert activity2.order == 2

    def test_unique_together_constraint(self, competence):
        LearningActivity.objects.create(
            specific_competence=competence,
            name="Multiplication"
        )
        with pytest.raises(Exception):
            LearningActivity.objects.create(
                specific_competence=competence,
                name="Multiplication"
            )

    def test_str_method(self, competence):
        activity = LearningActivity.objects.create(
            specific_competence=competence,
            name="Division Activity Example"
        )
        expected = f"{activity.name[:50]}... ({competence})"
        assert str(activity) == expected

    def test_order_is_filtered_by_specific_competence(self, main_competence):
        # First SpecificCompetence
        sc1 = SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="Competence 1"
        )
        sc2 = SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="Competence 2"
        )

        activity1 = LearningActivity.objects.create(
            specific_competence=sc1,
            name="Activity 1"
        )
        activity2 = LearningActivity.objects.create(
            specific_competence=sc1,
            name="Activity 2"
        )

        # Second SpecificCompetence
        sc3 = SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="Competence 3"
        )
        activity3 = LearningActivity.objects.create(
            specific_competence=sc3,
            name="Activity 3"
        )

        # Ensure order is independent per SpecificCompetence
        assert activity1.order == 1
        assert activity2.order == 2
        assert activity3.order == 1