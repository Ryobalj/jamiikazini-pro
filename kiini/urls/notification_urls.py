# kiini/urls/notification_urls.py

from rest_framework.routers import DefaultRouter
from kiini.views.notification_views import NotificationViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
urlpatterns = router.urls
