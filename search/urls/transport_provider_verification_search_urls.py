# search/urls/transport_provider_verification_urls.py

from django.urls import path
from search.views.transport_provider_verification_search_view import TransportProviderVerificationSearchView

urlpatterns = [
    path('transport-verifications/', TransportProviderVerificationSearchView.as_view(), name='search-transport-verifications'),
]