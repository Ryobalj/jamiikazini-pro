# businesses/admins/branch_admin.py

from django.contrib import admin
from businesses.models.branch import Branch

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'location', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'business')
    search_fields = ('name', 'business__name', 'location')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)