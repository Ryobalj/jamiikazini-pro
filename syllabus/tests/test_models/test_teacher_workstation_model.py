# syllabus/tests/test_models/test_teacher_workstation_model.py

import pytest
from django.db.models.signals import post_save
from syllabus.models.teacher_workstation import TeacherWorkStation
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.signals import create_or_reactivate_wallet

@pytest.mark.django_db
class TestTeacherWorkStationModel:

    @pytest.fixture(autouse=True)
    def disable_wallet_signal(self):
        """
        Disable the Wallet post_save signal during these tests to avoid
        duplicate wallet creation errors.
        """
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
        """
        Fresh user kwa kila test. Wallet itaundwa manually ili kuzuia conflicts.
        """
        user = user_factory(role="CLIENT")
        Wallet.objects.get_or_create(user=user)  # Ensure wallet exists
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

    def test_create_workstation(self, workstation):
        assert workstation.id is not None
        assert workstation.school_name == "Shule ya Msingi Mzingi"
        assert workstation.district == "Mkinga"
        assert workstation.ward == "Parungu"
        assert workstation.region == "Tanga"
        assert workstation.is_active is True

    def test_default_is_active(self, user):
        ws = TeacherWorkStation.objects.create(
            teacher=user,
            school_name="Shule ya Mawasiliano",
            district="Korogwe",
        )
        assert ws.is_active is True

    def test_optional_fields(self, user):
        ws = TeacherWorkStation.objects.create(
            teacher=user,
            school_name="Shule ya Mawasiliano",
            district="Korogwe",
            ward=None,
            region=None,
        )
        assert ws.ward is None
        assert ws.region is None

    def test_string_representation(self, workstation):
        teacher_name = workstation.teacher.get_full_name() or workstation.teacher.email
        expected = f"{teacher_name} @ Shule ya Msingi Mzingi (Mkinga)"
        assert str(workstation) == expected

    def test_one_teacher_cannot_have_two_workstations(self, user):
        TeacherWorkStation.objects.create(
            teacher=user,
            school_name="Shule A",
            district="Mkinga",
        )

        with pytest.raises(Exception):
            TeacherWorkStation.objects.create(
                teacher=user,
                school_name="Shule B",
                district="Tanga",
            )