# search/urls/syllabus_search_urls.py
from django.urls import path
from search.views.syllabus_search_views import SyllabusSearchAPIView

urlpatterns = [
    path("syllabus-search/", SyllabusSearchAPIView.as_view(), name="syllabus-search"),
]