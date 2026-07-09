# syllabus/tests/test_serializers/test_specific_learning_activity_serializer.py

import pytest
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.specific_learning_activity import SpecificLearningActivity
from syllabus.serializers.specific_learning_activity_serializer import SpecificLearningActivitySerializer

@pytest.mark.django_db
class TestSpecificLearningActivitySerializer:

    # ----------------------------
    # Fixtures
    # ----------------------------
    @pytest.fixture
    def competence(self, main_competence_obj):
        return SpecificCompetence.objects.create(name="Math Competence", main_competence=main_competence_obj)

    @pytest.fixture
    def learning_activity(self, competence):
        return LearningActivity.objects.create(
            specific_competence=competence,
            name="Addition Activity"
        )

    @pytest.fixture
    def specific_activity(self, learning_activity):
        return SpecificLearningActivity.objects.create(
            learning_activity=learning_activity,
            name="Add numbers up to 10",
            method="Demonstration",
            assessment_criteria="Solve 10 exercises",
            teaching_aids=["Charts"],
            references=["Textbook"],
            periods=2
        )

    # ----------------------------
    # Tests
    # ----------------------------
    def test_valid_serializer_create(self, learning_activity):
        data = {
            "learning_activity": learning_activity.id,
            "name": "Advanced Addition",
            "method": "Demonstration",
            "assessment_criteria": "Solve exercises",
            "teaching_aids": ["Charts"],
            "references": ["Textbook"],
            "periods": 2,
        }
        serializer = SpecificLearningActivitySerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.name == "Advanced Addition"
        assert instance.learning_activity == learning_activity

    def test_name_validation_empty(self, learning_activity):
        data = {
            "learning_activity": learning_activity.id,
            "name": "   ",
            "method": "Demonstration",
            "periods": 1,
        }
        serializer = SpecificLearningActivitySerializer(data=data)
        assert not serializer.is_valid()
        assert ("cannot be empty" in str(serializer.errors)) or ("blank" in str(serializer.errors))

    def test_method_validation_empty(self, learning_activity):
        data = {
            "learning_activity": learning_activity.id,
            "name": "Multiplication",
            "method": "   ",
            "periods": 1,
        }
        serializer = SpecificLearningActivitySerializer(data=data)
        assert not serializer.is_valid()
        assert ("cannot be empty" in str(serializer.errors)) or ("blank" in str(serializer.errors))

    def test_periods_validation_zero_or_negative(self, learning_activity):
        for value in [0, -1]:
            data = {
                "learning_activity": learning_activity.id,
                "name": "Division",
                "method": "Lecture",
                "periods": value,
            }
            serializer = SpecificLearningActivitySerializer(data=data)
            assert not serializer.is_valid()
            assert ("at least 1" in str(serializer.errors)) or ("greater than" in str(serializer.errors)) or ("periods" in str(serializer.errors))

    def test_unique_together_validation(self, specific_activity):
        # Trying to create duplicate name under same learning activity
        data = {
            "learning_activity": specific_activity.learning_activity.id,
            "name": specific_activity.name,  # duplicate
            "method": "Group work",
            "assessment_criteria": "Observation",
            "periods": 2,
        }
        serializer = SpecificLearningActivitySerializer(data=data)
        assert not serializer.is_valid()
        assert "already exists" in str(serializer.errors)

    def test_update_preserves_order(self, specific_activity):
        original_order = specific_activity.order
        data = {
            "name": "Updated Activity Name",
            "periods": 3,
        }
        serializer = SpecificLearningActivitySerializer(specific_activity, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.name == "Updated Activity Name"
        assert updated.periods == 3
        assert updated.order == original_order  # read-only preserved