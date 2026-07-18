# gov_integration/urls/__init__.py

from django.urls import path, include
from gov_integration.views.verification_request import VerificationRequestCreateView
from gov_integration.views.verification_status_update import VerificationStatusUpdateView
from gov_integration.views.verification_summary import VerificationSummaryView
from gov_integration.views.country_config import CountryListView
from gov_integration.views.service_type import ServiceTypeListView
from gov_integration.views.verification_list import VerificationRequestListView
from gov_integration.views.transport_verification_views import (
    NIDAVerificationView,
    DriverLicenseVerificationView,
    BusinessLicenseVerificationView,
    LatraLicenseVerificationView
)
from gov_integration.views.business_verification_views import (
    BusinessVerificationRequestView,
    BusinessVerificationStatusView,
)


urlpatterns = [
    path('', include('gov_integration.urls.country_config_urls')),
    path('', include('gov_integration.urls.transport_verification_urls')),
    path('', include('gov_integration.urls.verification_urls')),

    path('verify/', VerificationRequestCreateView.as_view(), name='verification-request'),
    path('verify/list/', VerificationRequestListView.as_view(), name='verification-request-list'),
    path('verify/<uuid:request_id>/status/', VerificationStatusUpdateView.as_view(), name='verification-status-update'),
    path('verify/summary/', VerificationSummaryView.as_view(), name='verification-summary'),

    path('verify/nida/', NIDAVerificationView.as_view(), name='verify_nida'),
    path('verify/driver_license/', DriverLicenseVerificationView.as_view(), name='verify_driver_license'),
    path('verify/business_license/', BusinessLicenseVerificationView.as_view(), name='verify_business_license'),
    path('verify/latra_license/', LatraLicenseVerificationView.as_view(), name='verify_latra_license'),

    path('verify/business/<uuid:business_id>/license/', BusinessVerificationRequestView.as_view(), name='verify-business-license-request'),
    path('verify/business/<uuid:business_id>/status/', BusinessVerificationStatusView.as_view(), name='verify-business-status'),

    path('countries/', CountryListView.as_view(), name='country-list'),
    path('services/', ServiceTypeListView.as_view(), name='service-list'),

    # New unified verification endpoint
    path('verification/', include('gov_integration.urls.verification_urls')),


]

