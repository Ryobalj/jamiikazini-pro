# gov_integration/tests/test_views/test_multicountry_nin.py
#
# (a) Nchi zote 6 za EAC zinapita kwenye njia kuu ya NIN (/gov/verify_nin/),
# (b) njia hiyo sasa inatumia registry ya gov_api_config/verify_entity, na
# (c) production ni fail-closed: bila config ya mamlaka, uthibitisho
#     unashindwa badala ya mock ya mafanikio.

import pytest
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from gov_integration.helpers.verification import verify_entity

User = get_user_model()

VALID_NINS = {
    "TZ": "12345678901234567890",
    "KE": "12345678",
    "UG": "CM12345678901",
    "RW": "1234567890123456",
    "BI": "BDI1234567",
    "SS": "SSD1234567",
}


@pytest.mark.django_db
class TestMultiCountryNIN:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.url = reverse("gov_integration:national-id-verification")

    def _user(self, email):
        return User.objects.create_user(
            email=email, password="testpass123", full_name="Test User", role="CLIENT",
        )

    @override_settings(DJANGO_ENV="development")
    @pytest.mark.parametrize("country", list(VALID_NINS.keys()))
    def test_all_six_countries_verify_in_development(self, country):
        user = self._user(f"user_{country.lower()}@example.com")
        self.client.force_authenticate(user=user)
        response = self.client.post(self.url, {
            "country": country, "national_id": VALID_NINS[country],
        })
        assert response.status_code == status.HTTP_200_OK, response.data
        user.refresh_from_db()
        assert user.is_identity_verified is True

    @override_settings(DJANGO_ENV="development")
    def test_invalid_burundi_id_rejected(self):
        user = self._user("bi_invalid@example.com")
        self.client.force_authenticate(user=user)
        response = self.client.post(self.url, {"country": "BI", "national_id": "abc"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @override_settings(DJANGO_ENV="production")
    def test_production_fails_closed_without_authority_config(self):
        # Hakuna TZ_NIDA_API_URL/API_KEY kwenye env ya test - production
        # inapaswa kukataa badala ya kufaulisha kwa mock.
        user = self._user("prod_user@example.com")
        self.client.force_authenticate(user=user)
        response = self.client.post(self.url, {
            "country": "TZ", "national_id": VALID_NINS["TZ"],
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.is_identity_verified is False


class TestVerifyEntityFailClosed:

    @override_settings(DJANGO_ENV="production")
    def test_no_config_returns_failed_in_production(self):
        result = verify_entity("tz", "nida", {"national_id_number": "123"})
        assert result.get("status") == "failed"
        assert result.get("verified") is False

    @override_settings(DJANGO_ENV="development")
    def test_no_config_still_mocks_in_development(self):
        result = verify_entity("tz", "nida", {"national_id_number": "123"})
        assert result.get("status") == "success"
