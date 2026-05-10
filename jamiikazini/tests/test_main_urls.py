# jamiikazini/tests/test_main_urls.py

import pytest
from django.urls import reverse, resolve
from django.conf import settings
from django.test import Client
from django.contrib import admin
from jamiikazini import urls as project_urls


@pytest.mark.django_db
class TestProjectUrls:
    def setup_method(self):
        self.client = Client()

    def test_admin_url_is_configured(self):
        response = self.client.get("/admin/")
        assert response.status_code in [200, 302]  # 200 (if logged in), 302 (redirect to login)

    def test_api_url_is_included(self):
        response = self.client.get("/api/v1/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.skipif(not settings.DEBUG, reason="Swagger URLs only available in DEBUG mode")
    def test_swagger_urls_are_accessible_in_debug(self):
        response_swagger = self.client.get("/swagger/")
        response_redoc = self.client.get("/redoc/")
        response_schema = self.client.get("/swagger.json")

        assert response_swagger.status_code == 200
        assert response_redoc.status_code == 200
        assert response_schema.status_code == 200

    def test_error_handlers_are_set(self):
        assert hasattr(project_urls, "handler404")
        assert hasattr(project_urls, "handler403")
        assert hasattr(project_urls, "handler500")

        assert project_urls.handler404 == "jamiikazini.views.error_views.custom_404_view"
        assert project_urls.handler403 == "jamiikazini.views.error_views.custom_403_view"
        assert project_urls.handler500 == "jamiikazini.views.error_views.custom_500_view"