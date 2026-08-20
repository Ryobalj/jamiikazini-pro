# syllabus/urls/master_timetable_pdf_urls.py

from django.urls import path
from syllabus.views.master_timetable_views import (
    MasterTimetablePDFAPIView,
    MasterTimetableXLSXAPIView,
)

urlpatterns = [
    path("master-timetables/<uuid:roster_id>/pdf/", MasterTimetablePDFAPIView.as_view(), name="master-timetable-pdf"),
    path("master-timetables/<uuid:roster_id>/xlsx/", MasterTimetableXLSXAPIView.as_view(), name="master-timetable-xlsx"),
]
