# syllabus/tests/conftest.py
# Mnyororo wa fixtures: SyllabusVersion -> Subject -> ClassLevel -> SubjectVersion -> MainCompetence -> SpecificCompetence

import pytest


@pytest.fixture
def syl_subject(db):
    from syllabus.models.subject import Subject
    return Subject.objects.create(name="Hisabati", periods_per_week=5)


@pytest.fixture
def syl_class_level(db):
    from syllabus.models.class_level import ClassLevel
    return ClassLevel.objects.create(name="Darasa la Nne", order=4)


@pytest.fixture
def syl_syllabus_version(db):
    from syllabus.models.syllabus_version import SyllabusVersion
    return SyllabusVersion.objects.create(year=2026)


@pytest.fixture
def subject_version(db, syl_subject, syl_class_level, syl_syllabus_version):
    from syllabus.models.subject_version import SubjectVersion
    return SubjectVersion.objects.create(
        syllabus_version=syl_syllabus_version,
        subject=syl_subject,
        class_level=syl_class_level,
    )


@pytest.fixture
def main_competence_obj(db, subject_version):
    from syllabus.models.main_competence import MainCompetence
    return MainCompetence.objects.create(name="Umahiri Mkuu", subject_version=subject_version)
