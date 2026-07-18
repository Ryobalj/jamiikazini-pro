# logistics/urls/fare_proposal_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from logistics.views.fare_proposal_views import FareProposalViewSet

router = DefaultRouter()
router.register(r'fare-proposals', FareProposalViewSet, basename='fare-proposal')

urlpatterns = [
    path('', include(router.urls)),
]
