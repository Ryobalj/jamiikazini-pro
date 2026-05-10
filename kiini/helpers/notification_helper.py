# kiini/helpers/notification_helper.py

from kiini.models.notification import Notification

def notify_user(user, message):
    if user:
        Notification.objects.create(user=user, message=message)
