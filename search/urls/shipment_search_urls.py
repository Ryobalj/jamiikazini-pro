# search/urls/shipment_search_urls.py

from django.urls import path
from search.views.shipment_search_view import ShipmentSearchView

urlpatterns = [
    path("shipments/", ShipmentSearchView.as_view(), name="search-shipments"),
]