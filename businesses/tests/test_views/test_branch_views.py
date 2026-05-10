import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from accounts.models import User
from kiini.models.institution import Institution
from businesses.models.business import Business
from businesses.models.branch import Branch


@pytest.mark.django_db
class TestBranchViewSet:

    @pytest.fixture
    def setup_data(self):
        institution = Institution.objects.create(name="Jamii Org")
        admin_user = User.objects.create_user(
            email="admin@jamii.com",
            password="test123",
            full_name="Admin",
            role="INSTITUTION_ADMIN",
            institution=institution
        )
        other_user = User.objects.create_user(
            email="client@jamii.com",
            password="test123",
            full_name="Client",
            role="CLIENT",
            institution=institution
        )
        business = Business.objects.create(name="Huduma Pro", owner=admin_user, institution=institution)

        branch = Branch.objects.create(
            business=business,
            name="Tawi la Posta",
            description="Ofisi ya Posta",
            phone="0766000000",
            email="posta@huduma.com",
            is_active=True,
        )

        return {
            "admin_user": admin_user,
            "other_user": other_user,
            "business": business,
            "branch": branch
        }

    def get_url(self, business_id, branch_id=None):
        base = f"/api/v1/businesses/{business_id}/branches/"
        return base if branch_id is None else f"{base}{branch_id}/"

    def test_list_branches(self, setup_data):
        client = APIClient()
        client.force_authenticate(user=setup_data["admin_user"])

        url = self.get_url(setup_data["business"].id)
        res = client.get(url)

        assert res.status_code == status.HTTP_200_OK
        assert any(b["id"] == setup_data["branch"].id for b in res.data)

    def test_retrieve_branch(self, setup_data):
        client = APIClient()
        client.force_authenticate(user=setup_data["admin_user"])

        url = self.get_url(setup_data["business"].id, setup_data["branch"].id)
        res = client.get(url)

        assert res.status_code == status.HTTP_200_OK
        assert res.data["name"] == setup_data["branch"].name

    def test_create_branch_authorized(self, setup_data):
        client = APIClient()
        client.force_authenticate(user=setup_data["admin_user"])

        url = self.get_url(setup_data["business"].id)
        data = {
            "name": "Tawi Jipya",
            "description": "Maelezo ya tawi jipya",
            "location": None,
            "phone": "0744123456",
            "email": "tawi@huduma.com",
            "is_active": True,
            "services": [],
        }
        res = client.post(url, data, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        assert Branch.objects.filter(name="Tawi Jipya").exists()

    def test_create_branch_unauthorized(self, setup_data):
        client = APIClient()
        client.force_authenticate(user=setup_data["other_user"])

        url = self.get_url(setup_data["business"].id)
        data = {
            "name": "Tawi Fake",
            "description": "Hakuna ruhusa",
            "location": None,
            "phone": "0711000000",
            "email": "fake@huduma.com",
            "is_active": True,
            "services": [],
        }
        res = client.post(url, data, format="json")

        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_update_branch(self, setup_data):
        client = APIClient()
        client.force_authenticate(user=setup_data["admin_user"])

        url = self.get_url(setup_data["business"].id, setup_data["branch"].id)
        res = client.patch(url, {"name": "Tawi Kubwa"}, format="json")

        assert res.status_code == status.HTTP_200_OK
        setup_data["branch"].refresh_from_db()
        assert setup_data["branch"].name == "Tawi Kubwa"

    def test_delete_branch(self, setup_data):
        client = APIClient()
        client.force_authenticate(user=setup_data["admin_user"])

        url = self.get_url(setup_data["business"].id, setup_data["branch"].id)
        res = client.delete(url)

        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Branch.objects.filter(id=setup_data["branch"].id).exists()

    def test_unauthenticated_access_denied(self, setup_data):
        client = APIClient()
        url = self.get_url(setup_data["business"].id)
        res = client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
