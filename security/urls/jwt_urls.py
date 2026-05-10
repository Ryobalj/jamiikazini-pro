# security/urls/jwt_urls.py

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView,
    TokenVerifyView, TokenBlacklistView
)

app_name = "security"

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("token/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
]