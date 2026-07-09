# search/tests/test_business_search.py

import pytest
from django.conf import settings

# These tests index into a live Elasticsearch cluster; skip when ES is off (local dev).
if not getattr(settings, "ELASTICSEARCH_ENABLED", False):
    pytest.skip("Requires live Elasticsearch (ELASTICSEARCH_ENABLED=False)", allow_module_level=True)
from django.urls import reverse
from rest_framework.test import APIClient
from search.documents.business_document import BusinessDocument
from businesses.models import Business, BusinessCategory as Category
from accounts.models import User
from kiini.models import Institution
from search.serializers.business_search_serializer import BusinessSearchSerializer

from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import get_connection


@pytest.mark.django_db
class TestBusinessSearch:

    @pytest.fixture
    def setup_data(self):
        institution = Institution.objects.create(name="Jamii Kaskazini", domain="jamiikaskazini")
        user = User.objects.create(username="mteja", email="mteja@example.com", password="test1234")
        category = Category.objects.create(name="Hotel", slug="hotel", description="Sehemu za malazi")
        business = Business.objects.create(
            name="Arusha Palace Hotel",
            description="Huduma bora za hoteli",
            phone="0766778899",
            email="info@arusha.com",
            website="https://arusha.com",
            is_active=True,
            institution=institution,
            owner=user,
            category=category,
            location="SRID=4326;POINT(36.685 3.369)"  # Arusha
        )
        return business

    def test_document_indexing(self, setup_data):
        document = BusinessDocument()
        prepared = document.prepare(setup_data)
        assert prepared["name"] == "Arusha Palace Hotel"
        assert "category" in prepared
        assert "location" in prepared
        assert isinstance(prepared["location"], dict)

    def test_serializer_output(self, setup_data):
        doc = BusinessDocument()
        indexed = doc.prepare(setup_data)
        serializer = BusinessSearchSerializer(indexed)
        data = serializer.data

        assert data["name"] == "Arusha Palace Hotel"
        assert "category" in data
        assert "location" in data

    def test_search_view_query(self, setup_data):
        client = APIClient()

        # Ensure data is indexed
        BusinessDocument().update(setup_data)
        bulk(get_connection(), BusinessDocument()._indexing_actions([setup_data]))
        BusinessDocument().refresh()

        url = reverse('business-search-list')
        response = client.get(url, {'q': 'hoteli'})
        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert any("Arusha" in b["name"] for b in response.data)

    def test_search_view_with_location_filter(self, setup_data):
        client = APIClient()

        BusinessDocument().update(setup_data)
        bulk(get_connection(), BusinessDocument()._indexing_actions([setup_data]))
        BusinessDocument().refresh()

        url = reverse('business-search-list')
        response = client.get(url, {'lat': 3.37, 'lon': 36.68, 'radius': '50km'})
        assert response.status_code == 200
        assert len(response.data) >= 1