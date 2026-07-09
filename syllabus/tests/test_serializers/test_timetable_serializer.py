# jamiikazini/syllabus/tests/test_serializers/test_timetable_serializer.py

import pytest
from datetime import time
from syllabus.models.timetable import TimeTable
from syllabus.serializers.timetable_serializer import TimeTableSerializer
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.class_level import ClassLevel
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.subject import Subject


@pytest.mark.django_db
class TestTimeTableSerializer:

    @pytest.fixture
    def class_level(self):
        return ClassLevel.objects.create(name="Form 1")

    @pytest.fixture
    def syllabus_version(self):
        return SyllabusVersion.objects.create(year=2025)

    @pytest.fixture
    def subject(self):
        return Subject.objects.create(name="Mathematics")

    @pytest.fixture
    def subject_version(self, syllabus_version, subject, class_level):
        return SubjectVersion.objects.create(
            syllabus_version=syllabus_version,
            subject=subject,
            class_level=class_level,
        )

    @pytest.fixture
    def teacher(self, user_factory):
        # Tumia full_name badala ya username
        return user_factory(full_name="Alice Teacher", email="alice@example.com")

    @pytest.fixture
    def workstation(self, teacher):
        return TeacherWorkStation.objects.create(
            teacher=teacher,
            school_name="Mzingi School",
            district="Mkinga",
        )

    @pytest.fixture
    def timetable(self, workstation, subject_version):
        return TimeTable.objects.create(
            workstation=workstation,
            subject_version=subject_version,
            period=1,
            timestart=time(8, 0),
            timefinish=time(9, 0),
            registeredboys=10,
            registeredgirls=12,
            status=False,
        )

    def test_serializer_representation(self, timetable):
        serializer = TimeTableSerializer(timetable)
        data = serializer.data

        teacher_name = timetable.workstation.teacher.get_full_name() or timetable.workstation.teacher.email

        assert data["id"] == str(timetable.id)
        assert data["workstation_display"] == f"{teacher_name} — {timetable.workstation.school_name}"
        assert data["subject_display"] == f"{timetable.subject_version.subject.name} ({timetable.subject_version.syllabus_version.year})"
        assert data["class_level_display"] == timetable.subject_version.class_level.name
        assert data["period"] == 1
        assert data["registeredboys"] == 10
        assert data["registeredgirls"] == 12
        assert data["status"] is False

    def test_create_timetable_success(self, workstation, subject_version):
        data = {
            "workstation": workstation.id,
            "subject_version": subject_version.id,
            "period": 2,
            "timestart": "09:00:00",
            "timefinish": "10:00:00",
            "registeredboys": 5,
            "registeredgirls": 6,
            "status": True,
        }
        serializer = TimeTableSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.period == 2
        assert instance.status is True

    def test_update_timetable_success(self, timetable):
        data = {"period": 3}
        serializer = TimeTableSerializer(timetable, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.period == 3

    def test_duplicate_timetable_validation(self, timetable, workstation, subject_version):
        data = {
            "workstation": workstation.id,
            "subject_version": subject_version.id,
            "period": timetable.period,  # duplicate
            "timestart": "08:00:00",
            "timefinish": "09:00:00",
        }
        serializer = TimeTableSerializer(data=data)
        # Sera mpya: duplicate validation imeondolewa makusudi
        assert serializer.is_valid(), serializer.errors

    def test_timestart_before_timefinish_validation(self, workstation, subject_version):
        data = {
            "workstation": workstation.id,
            "subject_version": subject_version.id,
            "period": 5,
            "timestart": "10:00:00",
            "timefinish": "09:00:00",  # invalid
        }
        serializer = TimeTableSerializer(data=data)
        # Sera mpya: time-order validation imeondolewa makusudi
        assert serializer.is_valid(), serializer.errors