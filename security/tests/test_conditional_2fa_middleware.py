# security/tests/test_conditional_2fa_middleware.py

import json
import pytest
from django.test import RequestFactory, override_settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from kiini.models.institution import Institution
from security.middleware.conditional_2fa import Conditional2FAMiddleware

pytestmark = pytest.mark.django_db


def dummy_get_response(request):
    from django.http import JsonResponse
    return JsonResponse({"detail": "ok"}, status=200)


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def user():
    institution = Institution.objects.create(name="Middleware Test Org", domain="mwtest")
    return User.objects.create_user(
        email="mw2fa@example.com", password="pass1234",
        full_name="MW User", role="CLIENT", institution=institution,
    )


def _build_request(factory, path, user=None, bearer_token=None):
    request = factory.get(path)
    request.user = user or AnonymousUser()
    request.session = {}
    if bearer_token:
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {bearer_token}"
    return request


@override_settings(TESTING=False)
def test_unprotected_path_passes_through(factory):
    request = _build_request(factory, "/api/v1/businesses/")
    middleware = Conditional2FAMiddleware(dummy_get_response)
    response = middleware(request)
    assert response.status_code == 200


@override_settings(TESTING=False)
def test_exempt_currencies_path_passes_through_without_auth(factory):
    request = _build_request(factory, "/api/v1/payments/currencies/")
    middleware = Conditional2FAMiddleware(dummy_get_response)
    response = middleware(request)
    assert response.status_code == 200


@override_settings(TESTING=False)
def test_protected_path_without_any_auth_returns_401(factory):
    request = _build_request(factory, "/api/v1/payments/invoices/")
    middleware = Conditional2FAMiddleware(dummy_get_response)
    response = middleware(request)
    assert response.status_code == 401


@override_settings(TESTING=False)
def test_protected_path_with_valid_jwt_bearer_is_recognized_as_authenticated(factory, user):
    """
    Regression test: previously the middleware only checked session-based
    request.user, so a genuinely JWT-authenticated frontend request would be
    misread as anonymous and always get 401 - even for a real, valid token.
    Once the user is correctly resolved, an unverified-OTP user should get the
    2FA-required 403 (not the "no credentials" 401).
    """
    token = str(RefreshToken.for_user(user).access_token)
    request = _build_request(factory, "/api/v1/payments/invoices/", bearer_token=token)
    middleware = Conditional2FAMiddleware(dummy_get_response)
    response = middleware(request)
    assert response.status_code == 403
    assert json.loads(response.content).get("2fa_required") is True


@override_settings(TESTING=False)
def test_protected_path_with_invalid_jwt_bearer_returns_401(factory):
    request = _build_request(factory, "/api/v1/payments/invoices/", bearer_token="not-a-real-token")
    middleware = Conditional2FAMiddleware(dummy_get_response)
    response = middleware(request)
    assert response.status_code == 401
