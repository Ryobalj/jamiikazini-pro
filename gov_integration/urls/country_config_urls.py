# gov_integration/urls/country_config_urls.py

from django.urls import path
from gov_integration.views.country_config import CountryListView
from gov_integration.views.service_type import ServiceTypeListView

urlpatterns = [
    path('countries/', CountryListView.as_view(), name='country-list'),
    path('service-types/', ServiceTypeListView.as_view(), name='service-type-list'),
]