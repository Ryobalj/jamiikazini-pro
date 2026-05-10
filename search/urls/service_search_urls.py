# search/urls/service_search_urls.py

from django.urls import path
from search.views.service_search_view import ServiceSearchView

urlpatterns = [
    path("services/search/", ServiceSearchView.as_view(), name="service-search"),
]