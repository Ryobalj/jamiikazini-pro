# security/urls/authy_log.py

from django.urls import path
from security.views.auth_logs import LoginHistoryView

app_name = "security_log"

urlpatterns = [
    path("logs/", LoginHistoryView.as_view(), name="login_history"),
]

