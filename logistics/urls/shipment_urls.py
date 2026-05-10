# logistics/urls/shipment_urls.py

from rest_framework.routers import DefaultRouter
from logistics.views.shipment_views import ShipmentViewSet

router = DefaultRouter()
router.register(r'shipments', ShipmentViewSet, basename='shipment')

urlpatterns = router.urls