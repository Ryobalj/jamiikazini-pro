# kiini/serializers/notification_serializer.py

from rest_framework import serializers
from kiini.models.notification import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'notification_type', 'link', 'is_read', 'created_at']
        read_only_fields = ['id', 'message', 'notification_type', 'link', 'created_at']
