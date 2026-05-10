# payments/admin/audit_log_admin.py 

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from payments.models.audit_log import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "action",
        "content_type",
        "object_id",
        "short_description",
        "ip_address",
    )
    list_filter = ("action", "content_type", "user")
    search_fields = (
        "user__full_name",
        "content_type__model",
        "object_id",
        "description",
        "ip_address",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "user",
        "action",
        "content_type",
        "object_id",
        "description",
        "metadata",
        "ip_address",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (_("Audit Log Details"), {
            "fields": (
                "created_at",
                "user",
                "action",
                "content_type",
                "object_id",
                "description",
                "metadata",
                "ip_address",
            ),
        }),
    )

    def short_description(self, obj):
        if obj.description:
            return (obj.description[:47] + "...") if len(obj.description) > 50 else obj.description
        return "-"
    short_description.short_description = _("Description")