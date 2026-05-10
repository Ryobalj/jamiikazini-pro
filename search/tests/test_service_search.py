# search/tests/test_service_search.py

from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.gis.geos import Point

from kiini.models.institution import Institution
from businesses.models.business import Business
from businesses.models.service import Service
from businesses.models.category import BusinessCategory


class TestServiceSearch(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="HealthPlus")
        self.category = BusinessCategory.objects.create(name="Clinics", slug="clinics")

        self.business = Business.objects.create(
            name="MedCare",
            institution=self.institution,
            location=Point(39.2, -6.8),
            is_active=True
        )

        self.service = Service.objects.create(
            name="General Checkup",
            description="Basic medical checkup service",
            price=50000,
            billing_type="once",
            location_type="on_site",
            requires_booking=False,
            is_available=True,
            duration_minutes=30,
            business=self.business,
            category=self.category
        )

        self.url = "/search/services/search/"

    def test_service_search_by_name(self):
        response = self.client.get(self.url, {"q": "checkup"})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)
        self.assertIn("General Checkup", str(response.data["results"]))

    def test_service_search_by_location(self):
        response = self.client.get(self.url, {"lat": -6.8, "lon": 39.2})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_service_search_by_category(self):
        response = self.client.get(self.url, {"category_id": self.category.id})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_service_search_pagination(self):
        response = self.client.get(self.url, {"page": 1, "per_page": 5})
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertIn("page", response.data)