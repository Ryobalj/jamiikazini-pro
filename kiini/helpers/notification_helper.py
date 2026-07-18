from kiini.models.notification import Notification, NotificationType


def notify_user(user, message, notification_type=NotificationType.SYSTEM, link=None):
    if user:
        Notification.objects.create(
            user=user, message=message, notification_type=notification_type, link=link,
        )
