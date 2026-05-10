# logistics/urls/transport_request_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from logistics.views.transport_request_views import TransportRequestViewSet

router = DefaultRouter()
router.register(r'transport-requests', TransportRequestViewSet, basename='transportrequest')

urlpatterns = [
    path('', include(router.urls)),
]
