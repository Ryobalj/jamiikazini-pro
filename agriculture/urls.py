# agriculture/urls.py

from rest_framework.routers import DefaultRouter

from agriculture.views.harvest_contract_views import HarvestContractViewSet

router = DefaultRouter()
router.register(r"contracts", HarvestContractViewSet, basename="harvest-contract")

urlpatterns = router.urls
