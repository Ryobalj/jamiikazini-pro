# kiini/tests/test_institution_tier.py

import pytest
from rest_framework import status
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from kiini.models.institution_tier import InstitutionTier

@pytest.mark.django_db
def test_institution_tier_choices_endpoint(unique_user):
    client = APIClient()
    token = RefreshToken.for_user(unique_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    url = reverse("kiini:institutiontier-choices")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert any(item["value"] == "MICRO" for item in response.data)