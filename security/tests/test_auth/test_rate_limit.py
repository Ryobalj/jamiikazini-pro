# security/tests/test_auth/test_rate_limit.py

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from accounts.models import User
from kiini.models.institution import Institution
from security.authentication.throttling import JamiiThrottle

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

    def test_rate_limit_blocks_after_limit(self, create_user, mocker):
        # Weka rate ndogo (3/hour) moja kwa moja kwenye throttle - haitegemei
        # settings-mutation ambayo DRF hairekebishi kwenye nested dict
        mocker.patch.object(JamiiThrottle, "get_rate", return_value="3/hour")
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

    def test_rate_limit_resets_after_wait(self, create_user, mocker):
        client = APIClient()
        url = reverse("jamii_auth:unified_login")

        # Rate 2/min + saa inayodhibitiwa (badala ya time.sleep halisi ya sekunde 61)
        mocker.patch.object(JamiiThrottle, "get_rate", return_value="2/min")
        clock = {"now": 1_000_000.0}
        mocker.patch.object(JamiiThrottle, "timer", lambda self: clock["now"])

        payload = {
            "email": "ratelimit@example.com",
            "password": "wrong",
            "recaptcha_token": "PASSED",
        }

        for _ in range(2):
            client.post(url, payload, **{'HTTP_X_FORWARDED_FOR': '127.0.0.1'})

        # Jaribio la 3 linapaswa kuzuiwa
        response = client.post(url, payload, **{'HTTP_X_FORWARDED_FOR': '127.0.0.1'})
        assert response.status_code == 429

        # Sogeza saa mbele sekunde 61 ili dirisha la dakika moja li-expire
        clock["now"] += 61

        # Jaribio jipya baada ya "kusubiri" linapaswa kuruhusiwa (401, si 429)
        response = client.post(url, payload, **{'HTTP_X_FORWARDED_FOR': '127.0.0.1'})
        assert response.status_code == 401  # credentials bado si sahihi, but rate limit imepita