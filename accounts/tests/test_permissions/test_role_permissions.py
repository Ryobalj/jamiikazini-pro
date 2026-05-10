import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request
from django.contrib.auth import get_user_model
from accounts.permissions import (
    IsAdmin, IsInstitutionAdmin, IsProvider, IsTransporter, IsClient,
    IsOwnerOrAdmin, IsSameUserOrAdmin,
)
from rest_framework.views import APIView

User = get_user_model()


@pytest.fixture
def user_factory(db):
    def create_user(role, email=None):
        return User.objects.create_user(
            email=email or f"{role.lower()}@example.com",
            password="testpass123",
            full_name="Test User",
            role=role
        )
    return create_user


@pytest.fixture
def api_request_factory():
    return APIRequestFactory()


class DummyView(APIView):
    permission_classes = []


@pytest.mark.parametrize("permission_class, role", [
    (IsAdmin, "ADMIN"),
    (IsInstitutionAdmin, "INSTITUTION_ADMIN"),
    (IsProvider, "PROVIDER"),
    (IsTransporter, "TRANSPORTER"),
    (IsClient, "CLIENT"),
])
def test_has_permission_roles(permission_class, role, user_factory, api_request_factory):
    user = user_factory(role)
    req = api_request_factory.get("/")
    force_authenticate(req, user=user)
    request = Request(req)

    perm = permission_class()
    assert perm.has_permission(request, DummyView())

    # Wrong role
    wrong_role = "CLIENT" if role != "CLIENT" else "ADMIN"
    wrong_user = user_factory(wrong_role, email="wrong@example.com")
    req = api_request_factory.get("/")
    force_authenticate(req, user=wrong_user)
    request = Request(req)
    assert not perm.has_permission(request, DummyView())


def test_has_permission_anonymous_returns_false(api_request_factory):
    req = api_request_factory.get("/")
    request = Request(req)  # unauthenticated
    request.user = User()  # Mock user without auth

    perm = IsAdmin()
    assert not perm.has_permission(request, DummyView())


def test_is_owner_or_admin_permission(user_factory, api_request_factory):
    owner = user_factory("CLIENT")
    other_user = user_factory("CLIENT", email="other@example.com")
    admin = user_factory("ADMIN", email="admin@example.com")

    class Obj:
        def __init__(self, user):
            self.user = user

    obj = Obj(user=owner)
    perm = IsOwnerOrAdmin()

    req = api_request_factory.get("/")
    force_authenticate(req, user=owner)
    request = Request(req)
    assert perm.has_object_permission(request, DummyView(), obj)

    req = api_request_factory.get("/")
    force_authenticate(req, user=admin)
    request = Request(req)
    assert perm.has_object_permission(request, DummyView(), obj)

    req = api_request_factory.get("/")
    force_authenticate(req, user=other_user)
    request = Request(req)
    assert not perm.has_object_permission(request, DummyView(), obj)


def test_is_same_user_or_admin_permission(user_factory, api_request_factory):
    user = user_factory("CLIENT")
    other_user = user_factory("CLIENT", email="other@example.com")
    admin = user_factory("ADMIN", email="admin@example.com")

    perm = IsSameUserOrAdmin()

    req = api_request_factory.get("/")
    force_authenticate(req, user=user)
    request = Request(req)
    assert perm.has_object_permission(request, DummyView(), user)

    req = api_request_factory.get("/")
    force_authenticate(req, user=admin)
    request = Request(req)
    assert perm.has_object_permission(request, DummyView(), user)

    req = api_request_factory.get("/")
    force_authenticate(req, user=other_user)
    request = Request(req)
    assert not perm.has_object_permission(request, DummyView(), user)