# businesses/admins/category_admin.py

from django.contrib import admin
from businesses.models.category import BusinessCategory


@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent_name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    ordering = ('name',)
    readonly_fields = ('created_at',)

    fieldsets = (
        ("Basic Info", {
            'fields': ('name', 'slug', 'parent')
        }),
        ("Status", {
            'fields': ('is_active',)
        }),
        ("Timestamps", {
            'fields': ('created_at',)
        }),
    )