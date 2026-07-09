# search/tests/test_branch_search.py

import pytest
from django.conf import settings

# These tests index into a live Elasticsearch cluster; skip when ES is off (local dev).
if not getattr(settings, "ELASTICSEARCH_ENABLED", False):
    pytest.skip("Requires live Elasticsearch (ELASTICSEARCH_ENABLED=False)", allow_module_level=True)
from django.urls import reverse
from rest_framework.test import APIClient
from businesses.models.branch import Branch
from businesses.models.business import Business
from accounts.models import User
from businesses.models.service import Service
from search.documents.branch_document import BranchDocument
from search.serializers.branch_search_serializer import BranchSearchSerializer

from django.contrib.gis.geos import Point
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections


@pytest.mark.django_db
class TestBranchSearch:

    @pytest.fixture(autouse=True)
    def setup(self, django_user_model):
        self.client = APIClient()
        self.connection = connections.get_connection()
        BranchDocument.init()

        # Create dummy data
        self.user = django_user_model.objects.create_user(username="testuser", password="pass")
        self.business = Business.objects.create(name="Test Biz", created_by=self.user)
        self.service1 = Service.objects.create(name="Cleaning")
        self.service2 = Service.objects.create(name="Delivery")

        self.branch = Branch.objects.create(
            business=self.business,
            name="Downtown Branch",
            description="We clean and deliver",
            phone="123456789",
            email="branch@test.com",
            location=Point(39.279, -6.821),
            is_active=True
        )
        self.branch.services.set([self.service1, self.service2])

        # Index to Elasticsearch
        BranchDocument().update(self.branch)

    def test_branch_document_indexing(self):
        """Test if the branch was correctly indexed"""
        search = BranchDocument.search().query("match", name="Downtown")
        results = search.execute()
        assert len(results) > 0
        assert results[0].name == "Downtown Branch"

    def test_branch_serializer(self):
        """Test BranchSearchSerializer returns expected fields"""
        doc = BranchDocument.get(id=str(self.branch.id))
        data = BranchSearchSerializer(doc).data
        assert data["name"] == "Downtown Branch"
        assert isinstance(data["business"], dict)
        assert isinstance(data["services"], list)
        assert isinstance(data["location"], dict)

    def test_branch_search_view_without_query(self):
        """Test view returns results without query param"""
        response = self.client.get("/search/branches/")
        assert response.status_code == 200
        assert isinstance(response.data, list)

    def test_branch_search_view_with_query(self):
        """Test search view with a text query"""
        response = self.client.get("/search/branches/?q=clean")
        assert response.status_code == 200
        assert any("clean" in branch["description"].lower() for branch in response.data)

    def test_branch_search_with_geo_filter(self):
        """Test view with geo-distance filter"""
        response = self.client.get("/search/branches/?lat=-6.820&lon=39.280&radius=5km")
        assert response.status_code == 200
        assert len(response.data) > 0