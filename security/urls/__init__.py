# security/urls/__init__.py

from django.urls import path, include

urlpatterns = [
    path("", include("security.urls.jwt_urls", namespace="security_jwt")),
    path("", include("security.urls.auth_urls", namespace="jamii_auth")),
    path("", include("security.urls.auth_log", namespace="security_log")),
    path("", include("security.urls.otp_2fa_urls", namespace="jamii_2fa")),
    path("", include("security.urls.otp_urls", namespace="security_otp")),
    path("", include("security.urls.phone_verification_urls", namespace="security_phone")),

]