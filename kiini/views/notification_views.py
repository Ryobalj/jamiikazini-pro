# kiini/views/notification_views.py

from rest_framework import viewsets, permissions
from kiini.models.notification import Notification
from kiini.serializers.notification_serializers import NotificationSerializer

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
