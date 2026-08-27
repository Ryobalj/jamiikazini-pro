from django.contrib import admin
from ..models.platform_lock import PlatformLock


@admin.register(PlatformLock)
class PlatformLockAdmin(admin.ModelAdmin):
    list_display = ("is_locked", "updated_at")
    fields = ("is_locked", "message", "updated_at")
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        # Singleton - the one row is created automatically by PlatformLock.load().
        return not PlatformLock.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Skip the list page entirely - go straight to editing the single row.
        # Query the real row directly (not PlatformLock.load(), which returns
        # a cached SimpleNamespace with no .pk - that's a lightweight read-only
        # view for the request-path middleware, not a model instance).
        obj, _ = PlatformLock.objects.get_or_create(pk=1)
        from django.shortcuts import redirect
        return redirect("admin:kiini_platformlock_change", obj.pk)
