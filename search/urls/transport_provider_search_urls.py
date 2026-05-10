# search/urls/transport_provider_search_urls.py

from django.urls import path
from search.views.transport_provider_search_view import TransportProviderSearchView

urlpatterns = [
    path("transport-providers/", TransportProviderSearchView.as_view(), name="transport-provider-search"),
]