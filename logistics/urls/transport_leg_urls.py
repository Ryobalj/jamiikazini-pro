# logistics/urls/transport_leg_urls.py

from rest_framework.routers import DefaultRouter
from logistics.views.transport_leg_views import (
  TransportLegViewSet,
  LegStatusLogViewSet,
  )

router = DefaultRouter()
router.register(r'transport-legs', TransportLegViewSet, basename='transport-legs')
router.register(r'leg-status-logs', LegStatusLogViewSet, basename='leg-status-logs')

urlpatterns = router.urls