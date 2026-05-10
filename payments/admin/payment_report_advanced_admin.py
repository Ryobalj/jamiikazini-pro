# payments/admin/payment_report_advanced_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
import csv
import json
from payments.models.payment_report import PaymentReport
from datetime import datetime


class ReportTypeFilter(admin.SimpleListFilter):
    title = _("Aina ya Ripoti")
    parameter_name = "report_type"

    def lookups(self, request, model_admin):
        return PaymentReport.ReportType.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(report_type=self.value())
        return queryset


class StatusFilter(admin.SimpleListFilter):
    title = _("Hali ya Ripoti")
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return PaymentReport.Status.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(PaymentReport)
class PaymentReportAdmin(admin.ModelAdmin):
    list_display = (
        "report_type_display",
        "user",
        "status",
        "progress_display",
        "start_date",
        "end_date",
        "generated_at",
        "is_ready",
    )
    list_filter = (
        ReportTypeFilter,
        StatusFilter,
        "file_format",
        "start_date",
    )
    search_fields = (
        "user__username",
        "user__email",
        "report_type",
        "error_message",
    )
    readonly_fields = (
        "is_ready",
        "is_expired",
        "get_summary_statistics_display",
        "created_at",
        "updated_at",
        "generated_at",
        "expires_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    actions = ["export_as_csv", "regenerate_reports", "cancel_generation"]

    fieldsets = (
        (_("Taarifa za Msingi"), {
            "fields": (
                "user",
                "report_type",
                "file_format",
            )
        }),
        (_("Muda wa Data"), {
            "fields": (
                "start_date",
                "end_date",
            ),
            "description": _("Weka kipindi cha data unachotaka kuchambua.")
        }),
        (_("Hali na Maendeleo"), {
            "fields": (
                "status",
                "progress_percentage",
                "is_ready",
                "is_expired",
            )
        }),
        (_("Vichujio"), {
            "fields": ("filters",),
            "classes": ("collapse",),
            "description": _("Vigezo maalum vya kuchuja data ya ripoti.")
        }),
        (_("Matokeo"), {
            "fields": (
                "report_data_preview",
                "summary_preview",
                "get_summary_statistics_display",
                "download_url",
            ),
            "classes": ("collapse",),
        }),
        (_("Hitilafu"), {
            "fields": ("error_message",),
            "classes": ("collapse",),
        }),
        (_("Muda"), {
            "fields": (
                "generated_at",
                "expires_at",
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
    )

    # ---------------------------
    # Custom Display Methods
    # ---------------------------
    def report_type_display(self, obj):
        return obj.get_report_type_display()
    report_type_display.short_description = _("Aina ya Ripoti")

    def progress_display(self, obj):
        return f"{obj.progress_percentage}%"
    progress_display.short_description = _("Maendeleo")

    def is_ready(self, obj):
        return obj.is_ready
    is_ready.boolean = True
    is_ready.short_description = _("Iko Tayari")

    def get_summary_statistics_display(self, obj):
        stats = obj.get_summary_statistics()
        if stats:
            return _(
                "Malipo: {transactions}, Jumla: {amount}, Mafanikio: {success_rate}%, Wastani: {average}"
            ).format(
                transactions=stats['total_transactions'],
                amount=stats['total_amount'],
                success_rate=stats['success_rate'],
                average=stats['average_transaction'],
            )
        return _("Hakuna data ya muhtasari")
    get_summary_statistics_display.short_description = _("Takwimu Muhimu")

    def report_data_preview(self, obj):
        if obj.report_data:
            preview = str(obj.report_data)[:200] + "..." if len(str(obj.report_data)) > 200 else str(obj.report_data)
            return preview
        return _("Hakuna data bado")
    report_data_preview.short_description = _("Data ya Ripoti (Onesho)")

    def summary_preview(self, obj):
        if obj.summary:
            preview = str(obj.summary)[:150] + "..." if len(str(obj.summary)) > 150 else str(obj.summary)
            return preview
        return _("Hakuna muhtasari bado")
    summary_preview.short_description = _("Muhtasari (Onesho)")

    # ---------------------------
    # Custom Actions
    # ---------------------------
    def export_as_csv(self, request, queryset):
        """Toa ripoti zilizochaguliwa kama CSV"""
        # Weka tu ripoti zilizo tayari
        ready_reports = queryset.filter(status=PaymentReport.Status.COMPLETED)
        
        if not ready_reports:
            self.message_user(request, _("Hakuna ripoti zilizo tayari kwa upakualiji."), level=messages.WARNING)
            return

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="advanced_payment_reports.csv"'

        writer = csv.writer(response)
        writer.writerow([
            _("Aina ya Ripoti"),
            _("Mtumiaji"),
            _("Tarehe ya Mwanzo"),
            _("Tarehe ya Mwisho"),
            _("Hali"),
            _("Malipo Yote"),
            _("Kiasi Cha Jumla"),
            _("Kiwango cha Mafanikio"),
            _("Tarehe ya Kutengenezwa"),
        ])

        for report in ready_reports:
            stats = report.get_summary_statistics()
            writer.writerow([
                report.get_report_type_display(),
                report.user.username if report.user else _("Mfumo"),
                report.start_date.strftime("%Y-%m-%d"),
                report.end_date.strftime("%Y-%m-%d"),
                report.get_status_display(),
                stats.get('total_transactions', 0),
                stats.get('total_amount', 0),
                f"{stats.get('success_rate', 0)}%",
                report.generated_at.strftime("%Y-%m-%d %H:%M") if report.generated_at else _("Haijakamilika"),
            ])

        return response
    export_as_csv.short_description = _("Toa ripoti zilizochaguliwa kama CSV")

    def regenerate_reports(self, request, queryset):
        """Rudia kutengeneza ripoti zilizochaguliwa"""
        from jamiitasks.tasks.report_tasks import generate_payment_report_task
        
        regenerated = 0
        for report in queryset:
            if report.status in [PaymentReport.Status.FAILED, PaymentReport.Status.CANCELLED]:
                report.status = PaymentReport.Status.GENERATING
                report.progress_percentage = 0
                report.error_message = ""
                report.save()
                
                # Anzisha upya utengenezaji
                generate_payment_report_task.delay(str(report.id))
                regenerated += 1

        self.message_user(
            request, 
            _("Ripoti {count} zimeanzishwa upya kwa utengenezaji.").format(count=regenerated), 
            level=messages.SUCCESS
        )
    regenerate_reports.short_description = _("Rudia kutengeneza ripoti zilizochaguliwa")

    def cancel_generation(self, request, queryset):
        """Sitisha utengenezaji wa ripoti"""
        cancelled = 0
        for report in queryset:
            if report.status == PaymentReport.Status.GENERATING:
                report.status = PaymentReport.Status.CANCELLED
                report.save()
                cancelled += 1

        self.message_user(
            request, 
            _("Utengenezaji wa ripoti {count} umesitishwa.").format(count=cancelled), 
            level=messages.SUCCESS
        )
    cancel_generation.short_description = _("Sitisha utengenezaji wa ripoti")

    # ---------------------------
    # Override Methods
    # ---------------------------
    def get_queryset(self, request):
        """Boresha utendaji kwa kutumia select_related"""
        return super().get_queryset(request).select_related('user')

    def has_delete_permission(self, request, obj=None):
        """
        Weka vibali vya kufuta kwa ripoti zilizokwisha tu
        """
        if obj and obj.status == PaymentReport.Status.GENERATING:
            return False
        return super().has_delete_permission(request, obj)