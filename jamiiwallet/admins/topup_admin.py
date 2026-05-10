# jamiiwallet/admins/topup_admin.py

from django.contrib import admin, messages
from jamiiwallet.models.topup import TopUp
from django.utils.translation import gettext_lazy as _


@admin.register(TopUp)
class TopUpAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user', 'amount', 'channel', 'status', 'confirmed_at', 'created_at')
    search_fields = ('reference', 'user__email', 'user__full_name')
    list_filter = ('channel', 'status')
    readonly_fields = ('reference', 'created_at', 'confirmed_at')
    date_hierarchy = 'created_at'
    actions = ['mark_as_processing', 'mark_as_failed']

    @admin.action(description="Mark selected top-ups as PROCESSING")
    def mark_as_processing(self, request, queryset):
        updated = 0
        for topup in queryset:
            if topup.status != TopUp.TopUpStatus.PROCESSING:
                topup.mark_processing()
                updated += 1
        self.message_user(request, _(f"{updated} top-up(s) marked as PROCESSING."), messages.INFO)

    @admin.action(description="Mark selected top-ups as FAILED")
    def mark_as_failed(self, request, queryset):
        updated = 0
        for topup in queryset:
            if topup.status != TopUp.TopUpStatus.FAILED:
                topup.mark_failed()
                updated += 1
        self.message_user(request, _(f"{updated} top-up(s) marked as FAILED."), messages.WARNING)