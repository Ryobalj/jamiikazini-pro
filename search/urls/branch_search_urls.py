# search/urls/branch_search_urls.py
# Maelezo: URL routes kwa ajili ya search app

from django.urls import path
from search.views.branch_search_view import BranchSearchView

urlpatterns = [
    path('branches/', BranchSearchView.as_view(), name='branch-search'),
]