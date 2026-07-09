# search/tests/test_department_search.py

import pytest
from django.conf import settings

# These tests index into a live Elasticsearch cluster; skip when ES is off (local dev).
if not getattr(settings, "ELASTICSEARCH_ENABLED", False):
    pytest.skip("Requires live Elasticsearch (ELASTICSEARCH_ENABLED=False)", allow_module_level=True)
from django.urls import reverse
from rest_framework.test import APIClient
from search.documents.department_document import DepartmentDocument
from kiini.models.department import Department
from kiini.models.institution import Institution
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import get_connection

@pytest.mark.django_db
class TestDepartmentSearch:

    @pytest.fixture
    def setup_data(self):
        institution = Institution.objects.create(name="JKT Lugalo", domain="lugalo.jamiikazini")
        dept = Department.objects.create(
            name="Idara ya Tiba",
            institution=institution
        )
        return dept

    def test_document_indexing(self, setup_data):
        doc = DepartmentDocument()
        prepared = doc.prepare(setup_data)
        assert prepared["name"] == "Idara ya Tiba"
        assert prepared["institution"]["name"] == "JKT Lugalo"

    def test_search_view(self, setup_data):
        client = APIClient()

        DepartmentDocument().update(setup_data)
        bulk(get_connection(), DepartmentDocument()._indexing_actions([setup_data]))
        DepartmentDocument().refresh()

        url = reverse("department-search-list")
        response = client.get(url, {"q": "Tiba"})
        assert response.status_code == 200
        assert any("Tiba" in dept["name"] for dept in response.data)

    def test_search_with_institution_filter(self, setup_data):
        client = APIClient()

        DepartmentDocument().update(setup_data)
        bulk(get_connection(), DepartmentDocument()._indexing_actions([setup_data]))
        DepartmentDocument().refresh()

        url = reverse("department-search-list")
        response = client.get(url, {"institution_id": setup_data.institution.id})
        assert response.status_code == 200
        assert len(response.data) >= 1