# security/tests/test_auth/test_rate_limit.py

import pytest
import time
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from accounts.models import User
from kiini.models.institution import Institution

@pytest.mark.django_db
class TestRateLimiting:

    @pytest.fixture
    def institution(self):
        return Institution.objects.create(name="Test Institution", domain="testdomain.local")

    @pytest.fixture
    def create_user(self, institution):
        return User.objects.create_user(
            email="ratelimit@example.com",
            password="securepassword",
            full_name="Rate Limit Test",
            role="CLIENT",
            institution=institution
        )

    def test_rate_limit_blocks_after_limit(self, create_user):
        client = APIClient()
        url = reverse("jamii_auth:unified_login")

        # Tuma maombi 3 yenye password mbovu (limit ni 3/hour)
        for _ in range(3):
            response = client.post(
                url,
                {
                    "email": "ratelimit@example.com",
                    "password": "wrongpassword",
                    "recaptcha_token": "PASSED"  # ✅ For test bypass
                },
                **{'HTTP_X_FORWARDED_FOR': '127.0.0.1'}
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Jaribio la 4 linapaswa kuzuiwa (HTTP 429)
        response = client.post(
            url,
            {
                "email": "ratelimit@example.com",
                "password": "wrongpassword",
                "recaptcha_token": "PASSED"
            },
            **{'HTTP_X_FORWARDED_FOR': '127.0.0.1'}
        )
        assert response.status_code == 429  # ✅ Too Many Requests

    def test_rate_limit_resets_after_wait(self, create_user, settings):
        client = APIClient()
        url = reverse("jamii_auth:unified_login")

        # Override throttle limit temporarily
        settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['security_authentication_throttle'] = '2/min'

        for _ in range(2):
            client.post(
                url,
                {
                    "email": "ratelimit@example.com",
                    "password": "wrong",
                    "recaptcha_token": "PASSED"
                },
                **{'HTTP_X_FORWARDED_FOR': '127.0.0.1'}
            )

        # Jaribio la 3 linapaswa kuzuiwa
        response = client.post(
            url,
            {
                "email": "ratelimit@example.com",
                "password": "wrong",
                "recaptcha_token": "PASSED"
            },
            **{'HTTP_X_FORWARDED_FOR': '127.0.0.1'}
        )
        assert response.status_code == 429

        # Subiri kwa sekunde 61 ili limit i-expire
        time.sleep(61)

        # Jaribio jipya baada ya kusubiri linapaswa kuruhusiwa
        response = client.post(
            url,
            {
                "email": "ratelimit@example.com",
                "password": "wrong",
                "recaptcha_token": "PASSED"
            },
            **{'HTTP_X_FORWARDED_FOR': '127.0.0.1'}
        )
        assert response.status_code == 401  # ✅ credentials bado si sahihi, but rate limit imepita