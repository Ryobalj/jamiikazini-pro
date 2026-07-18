# construction/urls.py

from rest_framework.routers import DefaultRouter

from construction.views.construction_views import ConstructionProjectViewSet

router = DefaultRouter()
router.register(r"projects", ConstructionProjectViewSet, basename="construction-project")

urlpatterns = router.urls
