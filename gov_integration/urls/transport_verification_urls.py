# gov_integration/urls/transport_verification_urls.py

from django.urls import path
from gov_integration.views.transport_verification_views import (
    NIDAVerificationView,
    DriverLicenseVerificationView,
    BusinessLicenseVerificationView,
    LatraLicenseVerificationView,
)

urlpatterns = [
    path('verify/nida/', NIDAVerificationView.as_view(), name='verify-nida'),
    path('verify/driver-license/', DriverLicenseVerificationView.as_view(), name='verify-driver-license'),
    path('verify/business-license/', BusinessLicenseVerificationView.as_view(), name='verify-business-license'),
    path('verify/latra-license/', LatraLicenseVerificationView.as_view(), name='verify-latra-license'),
]