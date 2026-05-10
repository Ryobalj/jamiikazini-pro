# logistics/urls/transport_provider_verification_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from logistics.views.transport_provider_verification_views import TransportProviderVerificationViewSet

router = DefaultRouter()
router.register(r'transport-verifications', TransportProviderVerificationViewSet, basename='transport-verification')

urlpatterns = [
    path('', include(router.urls)),
]


