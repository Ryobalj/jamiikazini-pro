# search/tests/test_review_search.py

import pytest
from django.conf import settings

# These tests index into a live Elasticsearch cluster; skip when ES is off (local dev).
if not getattr(settings, "ELASTICSEARCH_ENABLED", False):
    pytest.skip("Requires live Elasticsearch (ELASTICSEARCH_ENABLED=False)", allow_module_level=True)
from django.urls import reverse
from rest_framework.test import APIClient
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections

from search.documents.review_document import ReviewDocument
from businesses.models import Review, Business, Product, Service
from accounts.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def es_client():
    return connections.get_connection()


@pytest.fixture
def sample_data(es_client):
    # Create user, business, product, service, review
    user = User.objects.create(username="john_doe", email="john@example.com")
    business = Business.objects.create(name="Test Biz")
    product = Product.objects.create(name="Product A", business=business)
    service = Service.objects.create(name="Service A", business=business)

    review = Review.objects.create(
        user=user,
        business=business,
        product=product,
        service=service,
        rating=5,
        content="Amazing service!",
        is_approved=True
    )

    # Index to Elasticsearch
    doc = ReviewDocument()
    doc.update(review)

    # Refresh index
    ReviewDocument._index.refresh()

    return {
        "review": review,
        "user": user,
        "business": business,
        "product": product,
        "service": service
    }


def test_review_document_indexing(sample_data):
    review = sample_data["review"]
    s = ReviewDocument.search().query("match", content="Amazing")
    results = s.execute()

    assert len(results) > 0
    assert any(hit.id == str(review.id) for hit in results)


def test_review_search_serializer(sample_data):
    from search.serializers.review_search_serializer import ReviewSearchSerializer
    review = sample_data["review"]

    search = ReviewDocument.search().query("match", content="Amazing")
    response = search.execute()

    serializer = ReviewSearchSerializer(response, many=True)
    assert len(serializer.data) > 0
    assert serializer.data[0]["content"] == "Amazing service!"


def test_review_search_view_returns_results(sample_data):
    client = APIClient()
    url = reverse('review-search-list')  # Ensure this matches name in review_search_urls.py

    response = client.get(url, {'q': 'amazing'})
    assert response.status_code == 200
    assert len(response.data) > 0
    assert response.data[0]['content'] == 'Amazing service!'


def test_review_search_with_no_results():
    client = APIClient()
    url = reverse('review-search-list')
    response = client.get(url, {'q': 'nonexistent'})
    assert response.status_code == 200
    assert response.data == []