# logistics/urls/transport_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from logistics.views.transport_provider_views import TransportProviderViewSet

router = DefaultRouter()
router.register(r'transport-providers', TransportProviderViewSet, basename='transport-provider')

urlpatterns = [
    path('', include(router.urls)),
]