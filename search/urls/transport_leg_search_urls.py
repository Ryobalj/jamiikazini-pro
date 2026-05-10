# search/urls/transport_leg_search_urls.py

from django.urls import path
from search.views.transport_leg_search_view import TransportLegSearchView

urlpatterns = [
    path("transport-legs/", TransportLegSearchView.as_view(), name="transport-leg-search"),
]