# gov_integration/tests/test_country_authority_mapping.py

from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import pytest

from gov_integration.helpers.verification import (
    national_id_authority_for,
    driver_license_authority_for,
    transport_license_authority_for,
    mock_response,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_national_id_authority_for_mapping():
    assert national_id_authority_for("TZ") == "nida"
    assert national_id_authority_for("KE") == "nrb"
    assert national_id_authority_for("UG") == "nira"
    assert national_id_authority_for("RW") == "nida"
    assert national_id_authority_for("BI") == "oni"
    assert national_id_authority_for("SS") == "nia"
    assert national_id_authority_for(None) == "nida"


def test_driver_license_authority_for_mapping():
    assert driver_license_authority_for("TZ") == "tra_driver"
    assert driver_license_authority_for("KE") == "ntsa"
    assert driver_license_authority_for("UG") == "ura_driver"
    assert driver_license_authority_for("RW") == "rnp_driver"
    assert driver_license_authority_for("BI") == "driver"
    assert driver_license_authority_for("SS") == "driver"


def test_transport_license_authority_for_mapping():
    assert transport_license_authority_for("TZ") == "latra"
    assert transport_license_authority_for("UG") == "transport"
    # KE inatumia mamlaka moja (NTSA) kwa driver license na transport permits
    # zote mbili - hakuna haja ya config mpya ya KE_TRANSPORT.
    assert transport_license_authority_for("KE") == "ntsa"
    assert transport_license_authority_for("RW") == "rura"
    assert transport_license_authority_for("BI") == "transport"
    assert transport_license_authority_for("SS") == "transport"


@pytest.mark.parametrize("code", ["nida", "nrb", "nira", "oni", "nia"])
def test_mock_response_recognizes_all_national_id_authorities(code):
    response = mock_response(code, {"national_id_number": "12345"})
    assert response["status"] == "success"
    assert "full_name" in response["data"]


class TestVerificationViewsRespectCountryCode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="gov-country@example.com", password="test123",
            full_name="Gov Country User", role="CLIENT",
        )
        self.client.force_authenticate(user=self.user)

    def test_nida_view_uses_kenya_authority(self):
        url = reverse("gov_integration:verify_nida")
        with patch("gov_integration.views.transport_verification_views.verify_entity") as mock_verify:
            mock_verify.return_value = {"status": "success"}
            self.client.post(url, {"national_id_number": "123456", "country_code": "ke"}, format="json")
        mock_verify.assert_called_once_with(
            country_code="ke", authority_code="nrb",
            payload={"national_id_number": "123456"}, user=self.user,
        )

    def test_nida_view_defaults_to_tz_authority(self):
        url = reverse("gov_integration:verify_nida")
        with patch("gov_integration.views.transport_verification_views.verify_entity") as mock_verify:
            mock_verify.return_value = {"status": "success"}
            self.client.post(url, {"national_id_number": "123456"}, format="json")
        mock_verify.assert_called_once_with(
            country_code="tz", authority_code="nida",
            payload={"national_id_number": "123456"}, user=self.user,
        )

    def test_driver_license_view_uses_uganda_authority(self):
        url = reverse("gov_integration:verify_driver_license")
        with patch("gov_integration.views.transport_verification_views.verify_entity") as mock_verify:
            mock_verify.return_value = {"status": "success"}
            self.client.post(url, {"license_number": "L123", "country_code": "ug"}, format="json")
        mock_verify.assert_called_once_with(
            country_code="ug", authority_code="ura_driver",
            payload={"license_number": "L123"}, user=self.user,
        )

    def test_latra_view_uses_uganda_transport_authority(self):
        url = reverse("gov_integration:verify_latra_license")
        with patch("gov_integration.views.transport_verification_views.verify_entity") as mock_verify:
            mock_verify.return_value = {"status": "success"}
            self.client.post(url, {"latra_license_number": "T123", "country_code": "ug"}, format="json")
        mock_verify.assert_called_once_with(
            country_code="ug", authority_code="transport",
            payload={"latra_license_number": "T123"}, user=self.user,
        )
