# kiini/models/notification.py

from django.db import models
from django.conf import settings


class NotificationType(models.TextChoices):
    ORDER = "ORDER", "Order"
    CHAT = "CHAT", "Chat"
    PAYMENT = "PAYMENT", "Payment"
    REQUEST = "REQUEST", "Request"
    SYSTEM = "SYSTEM", "System"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    notification_type = models.CharField(
        max_length=10, choices=NotificationType.choices, default=NotificationType.SYSTEM,
    )
    # Njia ya ndani ya app (mfano "/orders/<id>") ya kubofya kwenda - hiari,
    # baadhi ya arifa (mfano tangazo la jumla) hazina pa kwenda.
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.user}: {self.message[:50]}"

