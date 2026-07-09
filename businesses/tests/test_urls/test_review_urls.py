import pytest
from django.urls import reverse, resolve
from rest_framework.test import APIClient
from rest_framework import status
from businesses.views.review_views import ProductReviewViewSet

# Reviews only exist as nested resources: product-reviews / service-reviews.


@pytest.mark.django_db
class TestReviewURLs:
    def _kwargs(self, setup_review):
        product = setup_review["product"]
        return {"business_pk": product.business.pk, "product_slug": product.slug}

    def test_reverse_reviews_list(self, setup_review):
        url = reverse("businesses:product-reviews-list", kwargs=self._kwargs(setup_review))
        match = resolve(url)
        assert match.func.cls == ProductReviewViewSet

    def test_reverse_reviews_detail(self, setup_review):
        review = setup_review["review"]
        url = reverse(
            "businesses:product-reviews-detail",
            kwargs={**self._kwargs(setup_review), "pk": review.pk},
        )
        match = resolve(url)
        assert match.func.cls == ProductReviewViewSet

    def test_reviews_list_get(self, setup_review):
        client = APIClient()
        client.force_authenticate(user=setup_review["user"])
        url = reverse("businesses:product-reviews-list", kwargs=self._kwargs(setup_review))
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_reviews_create_without_auth(self, setup_review):
        client = APIClient()
        url = reverse("businesses:product-reviews-list", kwargs=self._kwargs(setup_review))
        payload = {"rating": 5, "content": "Hii ni review"}
        response = client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
