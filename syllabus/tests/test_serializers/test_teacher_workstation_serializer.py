# jamiikazini/syllabus/tests/test_serializers/test_teacher_workstation_serializer.py

import pytest
from django.db.models.signals import post_save
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.serializers.teacher_workstation_serializer import (
    TeacherMiniSerializer,
    TeacherWorkStationSerializer,
)
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.signals import create_or_reactivate_wallet

@pytest.mark.django_db
class TestTeacherMiniSerializer:

    def test_teacher_mini_serializer_representation(self, user_factory):
        user = user_factory()

        serializer = TeacherMiniSerializer(user)

        # Tumetumia full_name badala ya username
        assert serializer.data["id"] == str(user.id)
        assert serializer.data["full_name"] == user.full_name
        assert serializer.data["email"] == user.email


@pytest.mark.django_db
class TestTeacherWorkStationSerializer:

    @pytest.fixture(autouse=True)
    def disable_wallet_signal(self):
        """Disable Wallet post_save signal during these tests."""
        post_save.disconnect(
            receiver=create_or_reactivate_wallet,
            sender=Wallet._meta.get_field('user').remote_field.model
        )
        yield
        post_save.connect(
            receiver=create_or_reactivate_wallet,
            sender=Wallet._meta.get_field('user').remote_field.model
        )

    @pytest.fixture
    def user(self, user_factory):
        """Fresh user kwa kila test. Wallet itaundwa manually ili kuzuia conflicts."""
        user = user_factory(role="CLIENT")
        Wallet.objects.get_or_create(user=user)
        return user

    @pytest.fixture
    def workstation(self, user):
        return TeacherWorkStation.objects.create(
            teacher=user,
            school_name="Shule ya Msingi Mzingi",
            district="Mkinga",
            ward="Parungu",
            region="Tanga",
            is_active=True,
        )

    def test_school_name_too_short(self, user):
        data = {
            "teacher": user.id,
            "school_name": "AB",
            "district": "Mkinga",
        }

        serializer = TeacherWorkStationSerializer(data=data)

        assert not serializer.is_valid()
        assert "school_name" in serializer.errors
        assert "fupi sana" in str(serializer.errors["school_name"][0])

    def test_teacher_cannot_have_two_workstations(self, user):
        # Existing workstation
        TeacherWorkStation.objects.create(
            teacher=user,
            school_name="Alpha School",
            district="Mkinga",
        )

        data = {
            "teacher": user.id,
            "school_name": "Beta School",
            "district": "Mkinga",
        }

        serializer = TeacherWorkStationSerializer(data=data)

        assert not serializer.is_valid()
        assert "teacher" in serializer.errors
        # Convert ErrorDetail to string
        assert str(serializer.errors["teacher"][0]) == "Mwalimu huyu tayari ana workstation moja."

    def test_create_workstation_success(self, user):
        data = {
            "teacher": user.id,
            "school_name": "Mzingi School",
            "district": "Mkinga",
            "ward": "Parungu",
            "region": "Tanga",
            "is_active": True,
        }

        serializer = TeacherWorkStationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.school_name == "Mzingi School"
        assert instance.teacher == user

    def test_update_workstation_success(self, user):
        instance = TeacherWorkStation.objects.create(
            teacher=user,
            school_name="Old Name",
            district="Mkinga"
        )

        data = {
            "school_name": "New School",
            "district": "Mkinga",
        }

        serializer = TeacherWorkStationSerializer(instance, data=data, partial=True)

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()
        assert updated.school_name == "New School"

    def test_readonly_fields_cannot_be_modified(self, user):
        instance = TeacherWorkStation.objects.create(
            teacher=user,
            school_name="Alpha",
            district="Mkinga"
        )

        original_id = str(instance.id)

        data = {
            "id": "fake-id",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
        }

        serializer = TeacherWorkStationSerializer(instance, data=data, partial=True)

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()
        assert str(updated.id) == original_id  # unchanged

    def test_teacher_info_in_representation(self, user_factory):
        teacher = user_factory(full_name="Alice Example")
        instance = TeacherWorkStation.objects.create(
            teacher=teacher,
            school_name="Alpha",
            district="Mkinga"
        )

        serializer = TeacherWorkStationSerializer(instance)
        data = serializer.data

        assert "teacher_info" in data
        # Tumetumia full_name badala ya username
        assert data["teacher_info"]["full_name"] == teacher.full_name
        assert data["teacher_info"]["email"] == teacher.email