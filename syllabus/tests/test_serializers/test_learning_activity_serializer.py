# syllabus/tests/test_serializers/test_learning_activity_serializer.py

import pytest
from syllabus.models.main_competence import MainCompetence
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.learning_activity import LearningActivity
from syllabus.serializers.learning_activity_serializer import LearningActivitySerializer


@pytest.mark.django_db
class TestLearningActivitySerializer:

    # ----------------- Fixtures ----------------- #
    @pytest.fixture
    def main_competence(self, subject_version):
        """Fixture for creating a main competence."""
        return MainCompetence.objects.create(name="Mathematics", subject_version=subject_version)

    @pytest.fixture
    def specific_competence(self, main_competence):
        """Fixture for creating a specific competence linked to main competence."""
        return SpecificCompetence.objects.create(
            name="Algebra",
            main_competence=main_competence
        )

    # ----------------- Tests ----------------- #

    def test_serializer_create_valid(self, specific_competence):
        """Test creating a LearningActivity with valid data."""
        data = {
            "specific_competence": specific_competence.id,
            "name": "  Addition Activity  ",  # testing trimming
        }
        serializer = LearningActivitySerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()

        # Name should be trimmed
        assert instance.name == "Addition Activity"
        # Order auto-assigned by model
        assert instance.order == 1

    def test_serializer_name_cannot_be_empty(self, specific_competence):
        """Test that an empty name is invalid."""
        data = {"specific_competence": specific_competence.id, "name": "   "}
        serializer = LearningActivitySerializer(data=data)
        assert not serializer.is_valid()
        assert ("tupu" in str(serializer.errors)) or ("blank" in str(serializer.errors))

    def test_serializer_unique_name_within_competence(self, specific_competence):
        """Test that names are unique within the same specific competence."""
        LearningActivity.objects.create(
            specific_competence=specific_competence, 
            name="Multiplication"
        )
        data = {"specific_competence": specific_competence.id, "name": "multiplication"}
        serializer = LearningActivitySerializer(data=data)
        assert not serializer.is_valid()
        assert "tayari ipo kwa competence hii" in str(serializer.errors)

    def test_serializer_update_preserves_order(self, specific_competence):
        """Updating a LearningActivity should preserve its order."""
        activity = LearningActivity.objects.create(
            specific_competence=specific_competence,
            name="Activity A"
        )
        original_order = activity.order

        serializer = LearningActivitySerializer(
            activity, 
            data={"name": "Activity Updated"}, 
            partial=True
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()

        # Ensure order is preserved
        assert updated.order == original_order
        assert updated.name == "Activity Updated"