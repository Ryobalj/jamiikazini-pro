# security/urls/otp_2fa_urls.py

from django.urls import path
from security.views.otp_2fa_views import Enable2FAView, Verify2FAView

app_name = 'jamii_2fa'

urlpatterns = [
    path("setup/", Enable2FAView.as_view(), name="enable_2fa"),
    path("verify/", Verify2FAView.as_view(), name="verify_2fa"),

]



