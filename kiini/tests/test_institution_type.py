# kiini/tests/test_institution_type.py

import pytest
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from kiini.models.institution_type import InstitutionType


@pytest.mark.django_db
class TestInstitutionTypeViewSet:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, unique_user):
        self.client = api_client
        self.user = unique_user
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Create types
        InstitutionType.objects.create(name="COLLEGE", description="College")
        InstitutionType.objects.create(name="PRIMARY_SCHOOL", description="Primary School")

    def test_list_institution_types(self):
        url = reverse("kiini:institutiontype-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_get_single_institution_type(self):
        obj = InstitutionType.objects.first()
        url = reverse("kiini:institutiontype-detail", args=[str(obj.id)])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(obj.id)

    def test_choices_endpoint(self):
        url = reverse("kiini:institutiontype-choices")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert {"value": "COLLEGE", "label": "College"} in response.data