# security/urls/otp_urls.py

from django.urls import path
from security.views.otp_views import RequestOTPView, VerifyOTPView

app_name = "security_otp"

urlpatterns = [
    path("otp/request/", RequestOTPView.as_view(), name="request_otp"),
    path("otp/verify/", VerifyOTPView.as_view(), name="verify_otp"),
]