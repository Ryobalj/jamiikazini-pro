# jamiitasks/admins/task_log_admin.py

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from jamiitasks.models.task_log import TaskLog
import datetime
import json


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    """
    Enterprise-level Admin + Analytics Dashboard for Celery Task Logs.
    Features:
    - Color-coded statuses
    - Aggregated metrics (success/fail/retry rates)
    - Per-task trend charts
    - Read-only & optimized
    """

    list_display = (
        "colored_status",
        "task_name",
        "reference",
        "duration_display",
        "retries",
        "worker_id",
        "created_at",
    )
    list_filter = (
        "status",
        ("task_name", admin.AllValuesFieldListFilter),
        ("worker_id", admin.AllValuesFieldListFilter),
        "created_at",
    )
    search_fields = ("task_name", "task_id", "reference", "details")
    readonly_fields = (
        "task_name",
        "status",
        "details",
        "retries",
        "duration_ms",
        "worker_id",
        "task_id",
        "reference",
        "created_at",
        "updated_at",
        "chart_data_json",
    )
    ordering = ("-created_at",)
    list_per_page = 30
    date_hierarchy = "created_at"
    change_form_template = "admin/jamiitasks/tasklog/change_form_with_chart.html"

    # =============================
    # 🟩 DISPLAY HELPERS
    # =============================
    def colored_status(self, obj):
        colors = {
            "SUCCESS": "#22c55e",
            "FAILED": "#ef4444",
            "RETRYING": "#f59e0b",
            "STARTED": "#3b82f6",
            "SKIPPED": "#9ca3af",
            "NOT_FOUND": "#6b7280",
        }
        color = colors.get(obj.status.upper(), "#6b7280")
        return format_html('<strong style="color:{};">{}</strong>', color, obj.status)
    colored_status.short_description = _("Status")

    def duration_display(self, obj):
        return f"{obj.duration_ms:.1f} ms" if obj.duration_ms else "-"
    duration_display.short_description = _("Duration")

    # =============================
    # 🔒 PERMISSIONS
    # =============================
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser

    # =============================
    # 📊 DASHBOARD SUMMARY
    # =============================
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        qs = self.get_queryset(request)
        total = qs.count()
        success = qs.filter(status="SUCCESS").count()
        failed = qs.filter(status="FAILED").count()
        retrying = qs.filter(status="RETRYING").count()

        extra_context.update({
            "total_tasks": total,
            "success_rate": round((success / total) * 100, 1) if total else 0,
            "fail_rate": round((failed / total) * 100, 1) if total else 0,
            "retrying_count": retrying,
        })
        return super().changelist_view(request, extra_context=extra_context)

    # =============================
    # 📈 TREND DATA PER TASK
    # =============================
    def chart_data_json(self, obj):
        """
        Generate simple JSON data of status counts per day for a given task.
        Used in admin chart template.
        """
        start_date = datetime.date.today() - datetime.timedelta(days=7)
        qs = (
            TaskLog.objects.filter(task_name=obj.task_name, created_at__date__gte=start_date)
            .values("status", "created_at__date")
            .annotate(count=Count("id"))
            .order_by("created_at__date")
        )

        # Group by date for frontend
        trend_data = {}
        for row in qs:
            day = row["created_at__date"].strftime("%Y-%m-%d")
            trend_data.setdefault(day, {"SUCCESS": 0, "FAILED": 0, "RETRYING": 0})
            trend_data[day][row["status"]] = row["count"]

        data = [
            {"date": day, **counts}
            for day, counts in sorted(trend_data.items())
        ]
        return json.dumps(data, default=str)

    chart_data_json.short_description = _("Task Trend Data (JSON)")

