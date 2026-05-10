# syllabus/urls/scheme_urls.py
from django.urls import path
from syllabus.views.scheme_views import (
    SchemeCreateAPIView,
    SchemePreviewAPIView,
    SchemePDFDownloadAPIView,
    SchemeDebugAPIView
)

urlpatterns = [
    path("schemes/", SchemeCreateAPIView.as_view(), name="scheme-create"),
    path("schemes/preview/", SchemePreviewAPIView.as_view(), name="scheme-preview"),
    path("schemes/pdf/", SchemePDFDownloadAPIView.as_view(), name="scheme-pdf"),
    path("schemes/debug/", SchemeDebugAPIView.as_view(), name="scheme-debug"),
]