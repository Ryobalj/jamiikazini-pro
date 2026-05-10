# search/urls/department_search_urls.py

from django.urls import path
from search.views.department_search_view import DepartmentSearchView

urlpatterns = [
    path('departments/', DepartmentSearchView.as_view(), name='department-search-list'),
]