# accounts/urls.py

from django.urls import path
from .views import (
    RegisterView,
    user_profile,
    ChangePasswordView,
    UserDetailView,
    VerifyEmailView,
    MeView,
    ForgotPasswordView,
    ResetPasswordView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', user_profile, name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('user_detail/', UserDetailView.as_view(), name='user-detail'),
    path('verify-email/<int:user_id>/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('me/', MeView.as_view(), name='me'),

    # Forgot/Reset Password
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<int:user_id>/<str:token>/', ResetPasswordView.as_view(), name='reset-password'),
]