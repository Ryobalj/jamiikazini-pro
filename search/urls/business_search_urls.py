# search/urls/business_search_urls.py

from django.urls import path
from search.views.business_search_view import BusinessSearchView

urlpatterns = [
    path('', BusinessSearchView.as_view(), name='business-search-list'),
]