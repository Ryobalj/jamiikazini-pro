# syllabus/urls/quiz_urls.py

from django.urls import path

from syllabus.views.generated_paper_views import GeneratePaperAPIView, GeneratedPaperPDFDownloadAPIView

urlpatterns = [
    path("quiz/generate/", GeneratePaperAPIView.as_view(), name="quiz-generate"),
    path("quiz/<uuid:pk>/pdf/", GeneratedPaperPDFDownloadAPIView.as_view(), name="quiz-pdf"),
]
