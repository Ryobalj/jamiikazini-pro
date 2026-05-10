# gov_integration/urls/verification_urls.py

from django.urls import path
from gov_integration.views.verification_list import VerificationRequestListView
from gov_integration.views.verification_request import VerificationRequestCreateView
from gov_integration.views.verification_status_update import VerificationStatusUpdateView
from gov_integration.views.verification_summary import VerificationSummaryView
from gov_integration.views.verification_views import (
  EntityVerificationView,
  NationalIDVerificationView,
  )


urlpatterns = [
    path('verifications/', VerificationRequestListView.as_view(), name='verification-list'),
    path('verifications/create/', VerificationRequestCreateView.as_view(), name='verification-create'),
    path('verifications/status-update/', VerificationStatusUpdateView.as_view(), name='verification-status-update'),
    path('verifications/summary/', VerificationSummaryView.as_view(), name='verification-summary'),
    path('verify/entity/', EntityVerificationView.as_view(), name='verify-entity'),
    path('verify_nin/', NationalIDVerificationView.as_view(), name='national-id-verification'),

]

