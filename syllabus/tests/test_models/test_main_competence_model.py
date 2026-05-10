# syllabus/tests/test_models/test_main_competence_model.py

import pytest
from django.db import IntegrityError
from syllabus.models.main_competence import MainCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.subject import Subject
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.class_level import ClassLevel


@pytest.fixture
def subject_version(db):
    syllabus_v = SyllabusVersion.objects.create(year=2025)
    subject = Subject.objects.create(name="Mathematics")
    class_level = ClassLevel.objects.create(name="P1", order=1)
    return SubjectVersion.objects.create(
        syllabus_version=syllabus_v,
        subject=subject,
        class_level=class_level
    )


@pytest.mark.django_db
def test_auto_order_first_item(subject_version):
    mc = MainCompetence.objects.create(
        subject_version=subject_version,
        name="Competence A"
    )
    assert mc.order == 1


@pytest.mark.django_db
def test_auto_order_increment(subject_version):
    mc1 = MainCompetence.objects.create(
        subject_version=subject_version,
        name="Competence A"
    )
    mc2 = MainCompetence.objects.create(
        subject_version=subject_version,
        name="Competence B"
    )
    assert mc1.order == 1
    assert mc2.order == 2


@pytest.mark.django_db
def test_unique_together_constraint(subject_version):
    MainCompetence.objects.create(
        subject_version=subject_version,
        name="Duplicate Competence"
    )

    with pytest.raises(IntegrityError):
        MainCompetence.objects.create(
            subject_version=subject_version,
            name="Duplicate Competence"
        )


@pytest.mark.django_db
def test_order_not_reset_on_update(subject_version):
    mc = MainCompetence.objects.create(
        subject_version=subject_version,
        name="Competence A"
    )
    old_order = mc.order

    mc.name = "Updated Competence"
    mc.save()

    assert mc.order == old_order  # order stays same


@pytest.mark.django_db
def test_ordering_meta(subject_version):
    mc1 = MainCompetence.objects.create(
        subject_version=subject_version,
        name="C A"
    )
    mc2 = MainCompetence.objects.create(
        subject_version=subject_version,
        name="C B"
    )
    competences = list(MainCompetence.objects.order_by("subject_version", "order"))
    assert competences == [mc1, mc2]


@pytest.mark.django_db
def test_str_method(subject_version):
    mc_name = "This is a long competence description for testing string representation"
    mc = MainCompetence.objects.create(
        subject_version=subject_version,
        name=mc_name
    )
    expected = f"{mc_name[:50]}... ({subject_version})"
    assert str(mc) == expected


@pytest.mark.django_db
def test_foreign_key_relation(subject_version):
    mc = MainCompetence.objects.create(
        subject_version=subject_version,
        name="Competence A"
    )
    assert mc.subject_version == subject_version
    assert subject_version.main_competences.count() == 1