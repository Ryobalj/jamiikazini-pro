# search/urls/review_search_urls.py
# Maelezo: URLs za ReviewSearchView kwa ajili ya Elasticsearch search ya maoni

from django.urls import path
from search.views.review_search_view import ReviewSearchView

urlpatterns = [
    path('reviews/', ReviewSearchView.as_view(), name='review-search'),
]