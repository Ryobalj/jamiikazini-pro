# security/urls/phone_verification_urls.py

from django.urls import path
from security.views.phone_verification_views import RequestPhoneVerificationView, VerifyPhoneVerificationView

app_name = "security_phone"

urlpatterns = [
    path("phone/request/", RequestPhoneVerificationView.as_view(), name="request_phone_verification"),
    path("phone/verify/", VerifyPhoneVerificationView.as_view(), name="verify_phone_verification"),
]
