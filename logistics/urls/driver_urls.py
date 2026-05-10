# logistics/urls/driver_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from logistics.views.driver_views import DriverViewSet

router = DefaultRouter()
router.register(r'drivers', DriverViewSet, basename='driver')

urlpatterns = [
    path('', include(router.urls)),
]