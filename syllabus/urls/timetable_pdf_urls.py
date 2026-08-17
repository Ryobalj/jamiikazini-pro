# syllabus/urls/timetable_pdf_urls.py

from django.urls import path
from syllabus.views.timetable_views import (
    TeacherTimetablePDFAPIView, SchoolTimetablePDFAPIView,
    TeacherTimetableXLSXAPIView, SchoolTimetableXLSXAPIView,
)

urlpatterns = [
    path("timetables/pdf/", TeacherTimetablePDFAPIView.as_view(), name="timetable-pdf"),
    path("timetables/school-pdf/", SchoolTimetablePDFAPIView.as_view(), name="school-timetable-pdf"),
    path("timetables/xlsx/", TeacherTimetableXLSXAPIView.as_view(), name="timetable-xlsx"),
    path("timetables/school-xlsx/", SchoolTimetableXLSXAPIView.as_view(), name="school-timetable-xlsx"),
]
