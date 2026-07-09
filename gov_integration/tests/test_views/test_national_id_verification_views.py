from unittest.mock import patch as _patch
from security.authentication.throttling import JamiiThrottle
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.test import override_settings
from gov_integration.models.verification_request import VerificationRequest

User = get_user_model()


from rest_framework import status
from gov_integration.models.verification_request import VerificationRequest
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestNationalIDVerificationView:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            role='CLIENT'
        )
        self.url = reverse('gov_integration:national-id-verification')

    @override_settings(DJANGO_ENV="development")
    def test_successful_verification_tz(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "country": "TZ",
            "national_id": "12345678901234567890"
        }
        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_200_OK, f"Unexpected response: {response.data}"
        assert "message" in response.data, "Missing 'message' in response"
        assert response.data["message"] == "User successfully verified."

        self.user.refresh_from_db()
        assert self.user.is_verified is True
        assert self.user.national_id == "12345678901234567890"

        assert VerificationRequest.objects.filter(
            user=self.user,
            country="TZ",
            status="VERIFIED"
        ).exists()

    @override_settings(DJANGO_ENV="development")
    def test_invalid_tanzanian_id(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "country": "TZ",
            "national_id": "1234"
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Tanzanian NIDA must be 20 digits." in str(response.data)

    @override_settings(DJANGO_ENV="development")
    def test_already_verified_user(self):
        self.user.is_verified = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        data = {
            "country": "TZ",
            "national_id": "12345678901234567890"
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "User is already verified." in str(response.data)

    @override_settings(DJANGO_ENV="development")
    def test_unauthenticated_user(self):
        data = {
            "country": "TZ",
            "national_id": "12345678901234567890"
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @override_settings(DJANGO_ENV="development")
    @_patch.object(JamiiThrottle, 'THROTTLE_RATES', {'security_authentication_throttle': '3/min'})
    def test_throttle_limit(self):
        self.client.force_authenticate(user=self.user)
        for i in range(3):  # max allowed attempts (assuming limit is 3)
            self.client.post(self.url, {
                "country": "TZ",
                "national_id": "12345678901234567890"
            })

        response = self.client.post(self.url, {
            "country": "TZ",
            "national_id": "12345678901234567890"
        })

        assert response.status_code == 429
        assert "Request was throttled" in str(response.data)

