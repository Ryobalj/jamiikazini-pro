# syllabus/urls/my_subject_urls.py

from django.urls import path
from syllabus.views.my_subject_views import MySubjectsAPIView

urlpatterns = [
    path("my-subjects/", MySubjectsAPIView.as_view(), name="my-subjects"),
]