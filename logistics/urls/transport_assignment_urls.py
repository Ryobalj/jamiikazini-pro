# logistics/urls/transport_assignment_urls.py

from rest_framework.routers import DefaultRouter
from logistics.views.transport_assignment_views import TransportAssignmentViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r"assignments", TransportAssignmentViewSet, basename="assignment")

urlpatterns = [
    path('', include(router.urls)),
]
