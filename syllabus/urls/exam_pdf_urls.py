# syllabus/urls/exam_pdf_urls.py

from django.urls import path
from syllabus.views.exam_views import (
    ExamSubjectResultPDFAPIView, ExamClassReportPDFAPIView,
    ExamSubjectResultXLSXAPIView, ExamClassReportXLSXAPIView,
)

urlpatterns = [
    path("exams/pdf/subject/", ExamSubjectResultPDFAPIView.as_view(), name="exam-subject-pdf"),
    path("exams/pdf/class-report/", ExamClassReportPDFAPIView.as_view(), name="exam-class-report-pdf"),
    path("exams/xlsx/subject/", ExamSubjectResultXLSXAPIView.as_view(), name="exam-subject-xlsx"),
    path("exams/xlsx/class-report/", ExamClassReportXLSXAPIView.as_view(), name="exam-class-report-xlsx"),
]
