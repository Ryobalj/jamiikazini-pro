# security/urls/auth_urls.py

from django.urls import path
from security.views.security_auth import UnifiedLoginView, LogoutView

app_name = "jamii_auth"

urlpatterns = [
    path('login/', UnifiedLoginView.as_view(), name='unified_login'),
    path('logout/', LogoutView.as_view(), name='logout'),

]