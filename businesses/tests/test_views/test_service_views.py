import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.gis.geos import Point

from businesses.models.service import Service
from businesses.models.business import Business
from accounts.models import User
from kiini.models.institution import Institution


@pytest.mark.django_db
class TestServiceViewSet:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.institution = Institution.objects.create(name="Test Institution", domain="testinstitution")
        self.user = User.objects.create_user(
            email="admin@test.com",
            password="pass1234",
            role='INSTITUTION_ADMIN',
            institution=self.institution,
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

        self.business = Business.objects.create(
            name="Test Biz",
            owner=self.user,
            institution=self.institution,
            location=Point(39.28, -6.80),
        )

        self.service1 = Service.objects.create(name="Huduma A", business=self.business, price=1000)
        self.service2 = Service.objects.create(name="Huduma B", business=self.business, price=2000)

    def test_list_services(self):
        url = reverse("businesses:business-services-list", kwargs={"business_pk": self.business.pk})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) == 2

    def test_filter_services_by_business(self):
        url = reverse("businesses:business-services-list", kwargs={"business_pk": self.business.pk})
        response = self.client.get(url, {"business": self.business.id})
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert all(str(item["business"]) == str(self.business.id) for item in data)

    def test_create_service(self):
        url = reverse("businesses:business-services-list", kwargs={"business_pk": self.business.pk})
        data = {"name": "Huduma Mpya", "business": self.business.id, "price": "1000.00", "billing_type": "HOURLY", "location_type": "REMOTE"}
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Huduma Mpya"

    def test_nearby_services_valid(self):
        url = reverse("businesses:business-services-nearby", kwargs={"business_pk": self.business.pk})
        response = self.client.get(url, {"lat": -6.80, "lng": 39.28})
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert isinstance(data, list)

    def test_nearby_services_missing_params(self):
        url = reverse("businesses:business-services-nearby", kwargs={"business_pk": self.business.pk})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data

    def test_nearby_services_invalid_coords(self):
        url = reverse("businesses:business-services-nearby", kwargs={"business_pk": self.business.pk})
        response = self.client.get(url, {"lat": "bad", "lng": "data"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data