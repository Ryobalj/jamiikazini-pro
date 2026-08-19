# syllabus/urls/__init__.py

from django.urls import path, include

from .router import urlpatterns as base_routes
from .nested_routers import urlpatterns as nested_routes

from syllabus.urls.lesson_plan_urls import urlpatterns as lesson_plan_routes
from syllabus.urls.scheme_urls import urlpatterns as scheme_routes
from syllabus.urls.my_subject_urls import urlpatterns as my_subject_routes
from syllabus.urls.subscription_urls import urlpatterns as subscription_routes
from syllabus.urls.timetable_pdf_urls import urlpatterns as timetable_pdf_routes
from syllabus.urls.exam_pdf_urls import urlpatterns as exam_pdf_routes
from syllabus.urls.quiz_urls import urlpatterns as quiz_routes

urlpatterns = [
    # ===== TIMETABLE / EXAM PDF =====
    # Must come before the base router: literal 'timetables/pdf/' and
    # 'exams/pdf/...' would otherwise be swallowed by the router's
    # 'timetables/<pk>/' / 'exams/<pk>/' detail regex.
    path("", include(timetable_pdf_routes)),
    path("", include(exam_pdf_routes)),

    # ===== BASE ROUTER (CRUD / VIEWSETS) =====
    path("", include(base_routes)),

    # ===== NESTED ROUTES =====
    path("nested/", include(nested_routes)),

    # ===== AUTO GENERATORS =====
    path("", include(lesson_plan_routes)),
    path("", include(scheme_routes)),  # ✅ Includes all scheme endpoints

    # ===== TEACHER DASHBOARD =====
    path("", include(my_subject_routes)),

    # ===== SUBSCRIPTION =====
    path("", include(subscription_routes)),

    # ===== QUIZ / TEST / EXAMINATION GENERATOR =====
    path("", include(quiz_routes)),
]