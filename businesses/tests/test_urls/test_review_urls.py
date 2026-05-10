import pytest
from django.urls import reverse, resolve
from rest_framework.test import APIClient
from rest_framework import status
from businesses.views.review_views import ReviewViewSet


@pytest.mark.django_db
class TestReviewURLs:
    def test_reverse_reviews_list(self):
        """Hakikisha review list URL inapatikana na inaelekeza kwa ViewSet sahihi."""
        url = reverse("businesses:reviews-list")
        match = resolve(url)
        assert match.func.cls == ReviewViewSet

    def test_reverse_reviews_detail(self, setup_review):
        """Hakikisha review detail URL inapatikana na inaelekeza kwa ViewSet sahihi."""
        review = setup_review["review"]
        url = reverse("businesses:reviews-detail", kwargs={"pk": review.pk})
        match = resolve(url)
        assert match.func.cls == ReviewViewSet

    def test_reviews_list_get(self, db):
        """GET kwenye reviews list inapaswa kurudisha status 200."""
        client = APIClient()
        url = reverse("businesses:reviews-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_reviews_create_without_auth(self, db):
        """POST bila authentication inapaswa kurudisha status 401."""
        client = APIClient()
        url = reverse("businesses:reviews-list")
        payload = {"rating": 5, "content": "Hii ni review"}
        response = client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED