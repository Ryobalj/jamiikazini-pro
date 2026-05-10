# kiini/admin/notification_admin.py

from django.contrib import admin
from kiini.models.notification import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def short_message(self, obj):
        return obj.message[:50] + ("..." if len(obj.message) > 50 else "")
    short_message.short_description = 'Message'
