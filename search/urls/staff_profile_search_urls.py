# search/urls/staff_profile_search_urls.py

from django.urls import path
from search.views.staff_profile_search_view import StaffProfileSearchView

urlpatterns = [
    path('staff-profiles/', StaffProfileSearchView.as_view(), name='staff-profile-search'),
]