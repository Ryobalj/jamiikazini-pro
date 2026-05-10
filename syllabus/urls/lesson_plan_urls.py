# syllabus/urls/lesson_plan_urls.py

from django.urls import path
from syllabus.views.lesson_plan_views import AutoLessonPlanCreateAPIView

urlpatterns = [
    # Dual-format: JSON free / PDF premium
    path(
        "lesson-plans/auto/",
        AutoLessonPlanCreateAPIView.as_view(),
        name="lessonplan-auto-create",
    ),
]