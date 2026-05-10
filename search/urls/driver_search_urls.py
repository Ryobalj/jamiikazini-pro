# search/urls/driver_search_urls.py

from django.urls import path
from search.views.driver_search_view import DriverSearchView

urlpatterns = [
    path("drivers/", DriverSearchView.as_view(), name="driver-search"),
]