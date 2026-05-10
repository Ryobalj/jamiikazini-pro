import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
import pyotp

@pytest.mark.django_db
class Test2FAViews:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="2fauser@example.com", password="strongpassword123"
        )
        self.login()

    def login(self):
        self.client.force_authenticate(user=self.user)

    def test_get_2fa_qr_code_and_uri(self):
        url = reverse("jamii_2fa:enable_2fa")
        response = self.client.get(url)

        assert response.status_code == 200
        assert "otp_uri" in response.data
        assert "qr_code" in response.data

    def test_enable_2fa_with_valid_token(self):
        # Generate token manually after fetching secret
        secret = self.user.get_2fa_secret()
        token = pyotp.TOTP(secret).now()

        url = reverse("jamii_2fa:enable_2fa")
        response = self.client.post(url, {"token": token})

        assert response.status_code == 200
        self.user.refresh_from_db()
        assert self.user.is_2fa_enabled is True

    def test_enable_2fa_with_invalid_token(self):
        self.user.get_2fa_secret()  # Just to set the secret
        url = reverse("jamii_2fa:enable_2fa")
        response = self.client.post(url, {"token": "000000"})

        assert response.status_code == 400
        assert response.data["detail"] == "Invalid token."
        self.user.refresh_from_db()
        assert self.user.is_2fa_enabled is False

    def test_verify_2fa_token_valid(self):
        # Set secret and enable manually
        secret = pyotp.random_base32()
        self.user._2fa_secret = secret
        self.user.is_2fa_enabled = True
        self.user.save()

        token = pyotp.TOTP(secret).now()
        url = reverse("jamii_2fa:verify_2fa")
        self.client.logout()  # Public view

        response = self.client.post(url, {
            "email": self.user.email,
            "token": token
        })

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_verify_2fa_token_invalid(self):
        secret = pyotp.random_base32()
        self.user._2fa_secret = secret
        self.user.is_2fa_enabled = True
        self.user.save()

        url = reverse("jamii_2fa:verify_2fa")
        self.client.logout()

        response = self.client.post(url, {
            "email": self.user.email,
            "token": "123456"
        })

        assert response.status_code == 401
        assert "detail" in response.data