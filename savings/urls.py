# savings/urls.py

from rest_framework.routers import DefaultRouter

from savings.views.savings_views import SavingsGroupViewSet

router = DefaultRouter()
router.register(r"groups", SavingsGroupViewSet, basename="savings-group")

urlpatterns = router.urls
