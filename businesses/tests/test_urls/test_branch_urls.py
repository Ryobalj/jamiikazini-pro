import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from kiini.models.institution import Institution
from businesses.models.business import Business
from businesses.models.branch import Branch
from django.contrib.gis.geos import Point

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def institution():
    return Institution.objects.create(name="Test Institution", domain="test")


@pytest.fixture
def user(institution):
    return User.objects.create_user(
        email="admin@example.com",
        password="password123",
        institution=institution,
        role="INSTITUTION_ADMIN",
    )


@pytest.fixture
def business(user, institution):
    return Business.objects.create(
        name="Main Business",
        owner=user,
        institution=institution,
        is_active=True,
    )


@pytest.fixture
def branch(business):
    return Branch.objects.create(
        name="Main Branch",
        business=business,
        location=Point(39.28, -6.81)
    )


def test_branch_list_authenticated(api_client, user, business, branch):
    api_client.force_authenticate(user=user)
    url = reverse("businesses:business-branches-list", kwargs={"business_pk": business.pk})
    res = api_client.get(url)
    assert res.status_code == 200
    assert isinstance(res.data, list) or "results" in res.data
    data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
    assert any(str(b["id"]) == str(branch.id) for b in data)


def test_branch_list_unauthenticated(api_client, business):
    url = reverse("businesses:business-branches-list", kwargs={"business_pk": business.pk})
    res = api_client.get(url)
    assert res.status_code in [200, 401]


def test_branch_create_authenticated(api_client, user, business):
    api_client.force_authenticate(user=user)
    url = reverse("businesses:business-branches-list", kwargs={"business_pk": business.pk})
    data = {"name": "New Branch", "location": {"type": "Point", "coordinates": [39.28, -6.81]}}
    res = api_client.post(url, data, format="json")
    assert res.status_code == 201
    assert res.data["name"] == "New Branch"


def test_branch_create_unauthenticated(api_client, business):
    url = reverse("businesses:business-branches-list", kwargs={"business_pk": business.pk})
    data = {"name": "Fail Branch", "location": "Test"}
    res = api_client.post(url, data)
    assert res.status_code == 401


def test_branch_with_invalid_business(api_client, user):
    api_client.force_authenticate(user=user)
    url = reverse("businesses:business-branches-list", kwargs={"business_pk": "00000000-0000-0000-0000-000000000000"})
    res = api_client.get(url)
    assert res.status_code in [200, 404]  # 404 if no business exists with that ID