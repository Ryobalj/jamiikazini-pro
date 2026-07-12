# jamiiwallet/tests/test_beneficiary.py

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from jamiiwallet.models.beneficiary import Beneficiary

User = get_user_model()


@pytest.fixture
def owner(db):
    return User.objects.create_user(email="owner@example.com", password="testpass", full_name="Owner O")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="mama@example.com", password="testpass", full_name="Mama M")


@pytest.mark.django_db
def test_create_beneficiary_links_registered_user(owner, other_user):
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.post(
        reverse('wallet:beneficiary-list'),
        {"name": "Mama", "identifier": "mama@example.com"},
        format='json',
    )

    assert response.status_code == 201, response.content
    assert response.json()["is_registered"] is True

    beneficiary = Beneficiary.objects.get(owner=owner)
    assert beneficiary.linked_user_id == other_user.id


@pytest.mark.django_db
def test_create_beneficiary_unregistered_identifier(owner):
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.post(
        reverse('wallet:beneficiary-list'),
        {"name": "Fundi", "identifier": "+255700000000"},
        format='json',
    )

    assert response.status_code == 201, response.content
    assert response.json()["is_registered"] is False


@pytest.mark.django_db
def test_beneficiaries_scoped_to_owner(owner, other_user):
    Beneficiary.objects.create(owner=owner, name="Mama", identifier="mama@example.com")
    Beneficiary.objects.create(owner=other_user, name="Owner", identifier="owner@example.com")

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.get(reverse('wallet:beneficiary-list'))

    body = response.json()
    results = body.get("results", body) if isinstance(body, dict) else body
    assert len(results) == 1
    assert results[0]["name"] == "Mama"


@pytest.mark.django_db
def test_delete_beneficiary(owner):
    beneficiary = Beneficiary.objects.create(owner=owner, name="Mama", identifier="mama@example.com")
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.delete(reverse('wallet:beneficiary-detail', args=[beneficiary.id]))
    assert response.status_code == 204
    assert not Beneficiary.objects.filter(id=beneficiary.id).exists()
