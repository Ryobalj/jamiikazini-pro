# security/tests/test_conditional_2fa_decorator.py

import json
import pytest
from django.test import RequestFactory, override_settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from kiini.models.institution import Institution
from security.decorators import conditional_2fa_required, otp_required

pytestmark = pytest.mark.django_db


class DummyView:
    @conditional_2fa_required(action_type="admin_action")
    def create(self, request, *args, **kwargs):
        from django.http import JsonResponse
        return JsonResponse({"detail": "ok"}, status=200)

    @otp_required(scope="general")
    def sensitive(self, request, *args, **kwargs):
        from django.http import JsonResponse
        return JsonResponse({"detail": "ok"}, status=200)


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def user_no_2fa():
    institution = Institution.objects.create(name="Decorator Test Org", domain="dectest")
    return User.objects.create_user(
        email="dec2fa@example.com", password="pass1234",
        full_name="Decorator User", role="CLIENT", institution=institution,
        is_2fa_enabled=False,
    )


@pytest.fixture
def user_with_2fa():
    institution = Institution.objects.create(name="Decorator Test Org 2", domain="dectest2")
    return User.objects.create_user(
        email="dec2fa2@example.com", password="pass1234",
        full_name="Decorator User 2FA", role="CLIENT", institution=institution,
        is_2fa_enabled=True,
    )


def _build_request(factory, path="/api/v1/businesses/", user=None, bearer_token=None):
    request = factory.post(path)
    request.user = user or AnonymousUser()
    request.session = {}
    if bearer_token:
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {bearer_token}"
    return request


@override_settings(TESTING=False)
def test_no_auth_at_all_returns_401(factory):
    request = _build_request(factory)
    response = DummyView().create(request)
    assert response.status_code == 401


@override_settings(TESTING=False)
def test_jwt_authenticated_user_without_2fa_enabled_passes_through(factory, user_no_2fa):
    """
    Regression test: previously conditional_2fa_required only checked session-based
    request.user, so a genuinely JWT-authenticated frontend request was misread as
    anonymous and always got 401 - even for a real, valid token, and even when the
    user doesn't have 2FA enabled at all (which should never require OTP).
    """
    token = str(RefreshToken.for_user(user_no_2fa).access_token)
    request = _build_request(factory, bearer_token=token)
    response = DummyView().create(request)
    assert response.status_code == 200


@override_settings(TESTING=False)
def test_jwt_authenticated_user_with_2fa_enabled_requires_otp(factory, user_with_2fa):
    token = str(RefreshToken.for_user(user_with_2fa).access_token)
    request = _build_request(factory, bearer_token=token)
    response = DummyView().create(request)
    assert response.status_code == 403
    assert "2FA required" in json.loads(response.content).get("detail", "")


@override_settings(TESTING=False)
def test_otp_required_decorator_resolves_jwt_user(factory, user_no_2fa):
    token = str(RefreshToken.for_user(user_no_2fa).access_token)
    request = _build_request(factory, bearer_token=token)
    response = DummyView().sensitive(request)
    # No OTP token/session provided - should be a 403 (OTP required), not a 401
    # (which would mean the JWT user was never resolved in the first place).
    assert response.status_code == 403
