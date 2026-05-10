# security/urls/csrf.py

from django.urls import path
from security.views.csrf_view import get_csrf_token

urlpatterns = [
    path("csrf/", get_csrf_token, name="csrf_token"),
]