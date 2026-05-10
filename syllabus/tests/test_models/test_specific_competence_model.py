# jamiikazini/syllabus/tests/test_models/test_specific_competence_model.py

import pytest
from syllabus.models.main_competence import MainCompetence
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.subject import Subject
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.class_level import ClassLevel

@pytest.mark.django_db
class TestSpecificCompetenceModel:

    @pytest.fixture
    def subject_version(db):
        syllabus = SyllabusVersion.objects.create(year=2025)
        subject = Subject.objects.create(name="Science")
        class_level = ClassLevel.objects.create(name="Grade 4", order=1)
        return SubjectVersion.objects.create(
            syllabus_version=syllabus,
            subject=subject,
            class_level=class_level
        )

    @pytest.fixture
    def main_competence(self, subject_version):
        return MainCompetence.objects.create(
            subject_version=subject_version,
            name="Main Competence A"
        )

    def test_auto_order_on_create(self, main_competence):
        sc1 = SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="Specific A"
        )
        assert sc1.order == 1

        sc2 = SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="Specific B"
        )
        assert sc2.order == 2

    def test_unique_together(self, main_competence):
        SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="Duplicate Check"
        )

        with pytest.raises(Exception):
            # Violates unique_together
            SpecificCompetence.objects.create(
                main_competence=main_competence,
                name="Duplicate Check"
            )

    def test_order_preserved_on_update(self, main_competence):
        sc = SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="Test Competence"
        )

        old_order = sc.order
        sc.name = "Updated Name"
        sc.save()

        assert sc.order == old_order

    def test_str_representation(self, main_competence):
        sc = SpecificCompetence.objects.create(
            main_competence=main_competence,
            name="Competence Example Text For Display"
        )

        result = str(sc)
        assert "Competence Example Text For Display"[:50] in result
        assert str(main_competence) in result

    def test_model_meta(self):
        """Ensure meta config is correct for ordering & verbose names."""
        assert SpecificCompetence._meta.verbose_name == "Specific Competence"
        assert SpecificCompetence._meta.verbose_name_plural == "Specific Competences"
        assert SpecificCompetence._meta.ordering == ["main_competence", "order"]