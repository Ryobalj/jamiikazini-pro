import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from kiini.models.institution import Institution
from businesses.models.business import Business

pytestmark = pytest.mark.django_db


@pytest.fixture
def public_business():
    institution = Institution.objects.create(name="Institution Public", domain="public.jamiikazini.com")
    owner = User.objects.create_user(email="owner@biz.com", password="pass123", institution=institution)
    business = Business.objects.create(
        name="Public Biz",
        description="Visible to all",
        owner=owner,
        institution=institution,
        is_active=True,
    )
    return business


@pytest.fixture
def inactive_business():
    institution = Institution.objects.create(name="Inactive Inst", domain="inactive.jamiikazini.com")
    owner = User.objects.create_user(email="owner@inactive.com", password="pass123", institution=institution)
    business = Business.objects.create(
        name="Inactive Biz",
        owner=owner,
        institution=institution,
        is_active=False,
    )
    return business


def test_public_business_detail_view_success(public_business):
    url = reverse("businesses:public-business-detail", kwargs={"pk": public_business.pk})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == public_business.id
    assert response.data["name"] == public_business.name


def test_public_business_detail_view_not_found_for_inactive(inactive_business):
    url = reverse("businesses:public-business-detail", kwargs={"pk": inactive_business.pk})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_public_business_detail_view_invalid_id():
    url = reverse("businesses:public-business-detail", kwargs={"pk": 9999})
    response = APIClient().get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND