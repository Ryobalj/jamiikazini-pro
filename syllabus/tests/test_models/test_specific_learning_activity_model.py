# jamiikazini/syllabus/tests/test_models/test_specific_learning_activity_model.py

import pytest
from syllabus.models.specific_learning_activity import SpecificLearningActivity
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.main_competence import MainCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel
from syllabus.models.syllabus_version import SyllabusVersion


@pytest.mark.django_db
class TestSpecificLearningActivityModel:

    @pytest.fixture
    def specific_competence(self):
        syllabus = SyllabusVersion.objects.create(year=2025)
        subject = Subject.objects.create(name="Science")
        level = ClassLevel.objects.create(name="Grade 4", order=1)

        subject_version = SubjectVersion.objects.create(
            syllabus_version=syllabus,
            subject=subject,
            class_level=level
        )

        main_comp = MainCompetence.objects.create(
            subject_version=subject_version,
            name="Main Science Competence"
        )

        return SpecificCompetence.objects.create(
            main_competence=main_comp,
            name="Specific Science Competence"
        )

    @pytest.fixture
    def learning_activity(self, specific_competence):
        return LearningActivity.objects.create(
            specific_competence=specific_competence,
            name="Activity Parent"
        )

    def test_str_representation(self, learning_activity):
        obj = SpecificLearningActivity.objects.create(
            learning_activity=learning_activity,
            method="Method X",
            name="This is a very long activity name for testing __str__",
            assessment_criteria="Criteria",
            teaching_aids="Aids",
            references="Refs",
            periods=2,
        )
        assert obj.__str__().startswith("This is a very long activity name")
        assert learning_activity.name in obj.__str__()

    def test_order_auto_increment(self, learning_activity):
        obj1 = SpecificLearningActivity.objects.create(
            learning_activity=learning_activity,
            method="M1",
            name="Activity 1",
            assessment_criteria="C1",
            teaching_aids="T1",
        )
        obj2 = SpecificLearningActivity.objects.create(
            learning_activity=learning_activity,
            method="M2",
            name="Activity 2",
            assessment_criteria="C2",
            teaching_aids="T2",
        )
        assert obj1.order == 1
        assert obj2.order == 2

    def test_unique_together_constraint(self, learning_activity):
        SpecificLearningActivity.objects.create(
            learning_activity=learning_activity,
            method="M",
            name="Duplicate Name",
            assessment_criteria="C",
            teaching_aids="T",
        )
        with pytest.raises(Exception):
            SpecificLearningActivity.objects.create(
                learning_activity=learning_activity,
                method="M2",
                name="Duplicate Name",
                assessment_criteria="C2",
                teaching_aids="T2",
            )