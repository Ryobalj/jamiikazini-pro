# gov_integration/tests/test_views/test_duplicate_national_id.py
#
# NIDA/NIN moja = akaunti moja: uthibitisho unakataliwa kama kitambulisho
# tayari kimeunganishwa na akaunti nyingine (kinalinganishwa kupitia
# User.national_id_hash - fingerprint ya kudumu, si Fernet ciphertext).

import pytest
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from security.helpers.encryption import hash_data

User = get_user_model()

NIN_TZ = "12345678901234567890"


@pytest.mark.django_db
class TestOneAccountPerNationalID:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.first_user = User.objects.create_user(
            email="first@example.com", password="testpass123",
            full_name="First User", role="CLIENT",
        )
        self.second_user = User.objects.create_user(
            email="second@example.com", password="testpass123",
            full_name="Second User", role="CLIENT",
        )
        self.url = reverse("gov_integration:national-id-verification")

    def _verify(self, user, national_id=NIN_TZ, country="TZ"):
        self.client.force_authenticate(user=user)
        return self.client.post(self.url, {"country": country, "national_id": national_id})

    @override_settings(DJANGO_ENV="development")
    def test_verification_stores_hash(self):
        response = self._verify(self.first_user)
        assert response.status_code == status.HTTP_200_OK, response.data
        self.first_user.refresh_from_db()
        assert self.first_user.national_id_hash == hash_data(NIN_TZ)

    @override_settings(DJANGO_ENV="development")
    def test_same_nin_rejected_on_second_account(self):
        assert self._verify(self.first_user).status_code == status.HTTP_200_OK

        response = self._verify(self.second_user)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "akaunti nyingine" in str(response.data)

        self.second_user.refresh_from_db()
        assert self.second_user.is_identity_verified is False
        assert self.second_user.national_id_hash is None

    @override_settings(DJANGO_ENV="development")
    def test_different_nins_both_verify(self):
        assert self._verify(self.first_user).status_code == status.HTTP_200_OK
        response = self._verify(self.second_user, national_id="09876543210987654321")
        assert response.status_code == status.HTTP_200_OK, response.data
        self.second_user.refresh_from_db()
        assert self.second_user.is_identity_verified is True

    @override_settings(DJANGO_ENV="development")
    def test_hash_is_deterministic_and_normalized(self):
        # Ugandan NIN ina herufi - normalization (strip+upper) inazuia
        # 'cm12345678901' na 'CM12345678901' kuonekana kama NIN mbili tofauti.
        assert self._verify(self.first_user, national_id="CM12345678901", country="UG").status_code == status.HTTP_200_OK
        response = self._verify(self.second_user, national_id="cm12345678901", country="UG")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "akaunti nyingine" in str(response.data)

    def test_db_constraint_blocks_direct_duplicates(self):
        # Hata nje ya serializer (mf. admin/shell), DB unique constraint
        # inazuia NIN ileile kwenye akaunti mbili.
        from django.db import IntegrityError, transaction

        self.first_user.national_id = NIN_TZ
        self.first_user.save()
        self.second_user.national_id = NIN_TZ
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                self.second_user.save()
