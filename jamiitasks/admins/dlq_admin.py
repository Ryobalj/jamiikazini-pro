# jamiitasks/admins/dlq_admin.py

from django.contrib import admin
from jamiitasks.models.dead_letter import DeadLetterQueue

@admin.register(DeadLetterQueue)
class DeadLetterQueueAdmin(admin.ModelAdmin):
    list_display = ("id", "task_name", "task_id", "status", "attempts", "created_at", "last_attempt_at", "requeued")
    list_filter = ("status", "task_name", "requeued")
    search_fields = ("task_name", "task_id", "error", "metadata")
    readonly_fields = ("payload", "error", "traceback", "metadata", "created_at", "updated_at", "last_attempt_at", "requeued_at")
    actions = ["requeue_selected", "export_selected"]

    def requeue_selected(self, request, queryset):
        from jamiitasks.services.dead_letter_service import DeadLetterService
        ds = DeadLetterService()
        count = 0
        for dl in queryset:
            if not dl.requeued:
                ds.requeue(dl)
                count += 1
        self.message_user(request, f"Requeued {count} dead-letter(s).")
    requeue_selected.short_description = "Requeue selected dead letters"

    def export_selected(self, request, queryset):
        # simple JSON export action
        import json
        from django.http import HttpResponse
        data = []
        for dl in queryset:
            data.append({
                "id": str(dl.id),
                "task_name": dl.task_name,
                "task_id": dl.task_id,
                "payload": dl.payload,
                "error": dl.error,
                "traceback": dl.traceback,
                "attempts": dl.attempts,
                "metadata": dl.metadata,
                "created_at": dl.created_at.isoformat(),
            })
        resp = HttpResponse(json.dumps(data, indent=2), content_type="application/json")
        resp["Content-Disposition"] = "attachment; filename=dead_letters.json"
        return resp
    export_selected.short_description = "Export selected dead letters (JSON)"