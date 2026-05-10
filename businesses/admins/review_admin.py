# businesses/admins/review_admin.py

from django.contrib import admin
from businesses.models.review import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'rating', 'content_type', 'object_id',
        'is_approved', 'created_at'
    )
    list_filter = ('rating', 'is_approved', 'content_type')
    search_fields = ('user__full_name', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('user', 'rating', 'content', 'content_type', 'object_id', 'is_approved')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )