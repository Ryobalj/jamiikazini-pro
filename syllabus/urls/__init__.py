# syllabus/urls/__init__.py

from django.urls import path, include

from .router import urlpatterns as base_routes
from .nested_routers import urlpatterns as nested_routes

from syllabus.urls.lesson_plan_urls import urlpatterns as lesson_plan_routes
from syllabus.urls.scheme_urls import urlpatterns as scheme_routes
from syllabus.urls.my_subject_urls import urlpatterns as my_subject_routes

urlpatterns = [
    # ===== BASE ROUTER (CRUD / VIEWSETS) =====
    path("", include(base_routes)),

    # ===== NESTED ROUTES =====
    path("nested/", include(nested_routes)),

    # ===== AUTO GENERATORS =====
    path("", include(lesson_plan_routes)),
    path("", include(scheme_routes)),  # ✅ Includes all scheme endpoints

    # ===== TEACHER DASHBOARD =====
    path("", include(my_subject_routes)),
]