# payments/views/payment_report_views.py

import logging
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser

from payments.views.base import BaseCRUDViewSet
from payments.models.payment_report import PaymentReport
from payments.serializers.payment_report_serializer import (
    PaymentReportSerializer,
    PaymentReportSummarySerializer,
    PaymentReportCreateSerializer,
    PaymentReportUpdateSerializer,
    PaymentReportDataSerializer,
    PaymentReportFilterSerializer,
)

logger = logging.getLogger(__name__)


class PaymentReportViewSet(BaseCRUDViewSet):
    """
    ViewSet kamili ya usimamizi wa Payment Reports:
    - CRUD kamili
    - Filtering smart
    - Async generation
    - Stats na summaries
    """

    queryset = PaymentReport.objects.select_related("user").all()
    serializer_class = PaymentReportSerializer
    filterset_fields = ["report_type", "status", "file_format", "user"]
    ordering_fields = [
        "created_at",
        "start_date",
        "end_date",
        "progress_percentage",
        "generated_at",
    ]
    ordering = ["-created_at"]
    owner_field = "user"

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return PaymentReportSummarySerializer
        elif self.action == "create":
            return PaymentReportCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return PaymentReportUpdateSerializer
        elif self.action == "report_data":
            return PaymentReportDataSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """Apply filtering, ownership scope, and validation"""
        queryset = super().get_queryset()

        # 🔒 Restrict non-admin users to their own reports
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(user=user)

        # ✅ Safe filtering via validated serializer
        filter_serializer = PaymentReportFilterSerializer(data=self.request.query_params)
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data

            if filters.get("report_type"):
                queryset = queryset.filter(report_type=filters["report_type"])

            if filters.get("status"):
                queryset = queryset.filter(status=filters["status"])

            if filters.get("start_date"):
                queryset = queryset.filter(created_at__gte=filters["start_date"])

            if filters.get("end_date"):
                queryset = queryset.filter(created_at__lte=filters["end_date"])

            if filters.get("file_format"):
                queryset = queryset.filter(file_format=filters["file_format"])

        return queryset

    def perform_create(self, serializer):
        """Custom create with async generation trigger"""
        super().perform_create(serializer)
        report = serializer.instance
        self._trigger_report_generation(report)

    def _trigger_report_generation(self, report):
        """Trigger asynchronous report generation with logging"""
        try:
            from jamiitasks.tasks.payment_tasks import generate_report_data_task
            generate_report_data_task.delay(report.id)
            logger.info(f"Triggered async generation for PaymentReport {report.id}")
        except Exception as e:
            logger.error(f"Failed to start async report generation ({report.id}): {e}")
            report.mark_failed(_("Failed to start report generation: {}").format(str(e)))

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        """Return overall statistics (cached for performance)"""
        user = request.user
        cache_key = f"payment_report_stats_{user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        qs = self.filter_queryset(self.get_queryset())

        stats = qs.aggregate(
            total_reports=Count("id"),
            completed_reports=Count("id", filter=Q(status=PaymentReport.Status.COMPLETED)),
            failed_reports=Count("id", filter=Q(status=PaymentReport.Status.FAILED)),
            generating_reports=Count("id", filter=Q(status=PaymentReport.Status.GENERATING)),
            average_progress=Avg("progress_percentage"),
        )

        report_type_stats = qs.values("report_type").annotate(count=Count("id")).order_by("-count")

        formatted_type_stats = [
            {
                "report_type": stat["report_type"],
                "display_name": PaymentReport.ReportType(stat["report_type"]).label,
                "count": stat["count"],
            }
            for stat in report_type_stats
        ]

        data = {
            "overview": {
                "total_reports": stats.get("total_reports", 0),
                "completed_reports": stats.get("completed_reports", 0),
                "failed_reports": stats.get("failed_reports", 0),
                "generating_reports": stats.get("generating_reports", 0),
                "average_progress": round(stats.get("average_progress") or 0, 1),
            },
            "report_type_distribution": formatted_type_stats,
            "timestamp": timezone.now().isoformat(),
        }

        # Cache kwa dakika 5
        cache.set(cache_key, data, 300)
        return Response(data)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser], url_path="global-summary")
    def global_summary(self, request):
        """Admin-only global summary"""
        qs = PaymentReport.objects.all()

        summary = qs.aggregate(
            total_reports=Count("id"),
            total_users=Count("user", distinct=True),
            avg_progress=Avg("progress_percentage"),
        )

        return Response({
            "total_reports": summary["total_reports"],
            "total_users": summary["total_users"],
            "avg_progress": round(summary["avg_progress"] or 0, 1),
            "timestamp": timezone.now().isoformat(),
        })

    @action(detail=False, methods=["get"], url_path="my-reports")
    def my_reports(self, request):
        """Return only reports belonging to the current user"""
        queryset = self.filter_queryset(
            self.get_queryset().filter(user=request.user)
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PaymentReportSummarySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PaymentReportSummarySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="data")
    def report_data(self, request, pk=None):
        """Return only the report data, if ready"""
        report = self.get_object()

        if not report.is_ready:
            return Response({"detail": _("Report is not ready yet")}, status=status.HTTP_404_NOT_FOUND)

        if report.is_expired:
            return Response({"detail": _("Report has expired")}, status=status.HTTP_410_GONE)

        serializer = self.get_serializer(report)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="regenerate")
    def regenerate(self, request, pk=None):
        """Regenerate a completed or failed report"""
        report = self.get_object()

        if report.status not in [
            PaymentReport.Status.COMPLETED,
            PaymentReport.Status.FAILED,
        ]:
            return Response(
                {"detail": _("Can only regenerate completed or failed reports")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report.status = PaymentReport.Status.GENERATING
        report.progress_percentage = 0
        report.error_message = ""
        report.generated_at = None
        report.save()

        self._trigger_report_generation(report)

        return Response(
            {"detail": _("Report regeneration started"), "report_id": str(report.id)}
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """Cancel a report that is still generating"""
        report = self.get_object()

        if report.status != PaymentReport.Status.GENERATING:
            return Response(
                {"detail": _("Can only cancel reports that are generating")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report.status = PaymentReport.Status.CANCELLED
        report.error_message = _("Cancelled by user")
        report.save()

        logger.info(f"Payment report {report.id} cancelled by {request.user}")

        return Response(
            {"detail": _("Report cancelled successfully"), "report_id": str(report.id)}
        )

    @action(detail=False, methods=["get"], url_path="status-options")
    def status_options(self, request):
        """List available status options"""
        options = [
            {"value": v, "display_name": n}
            for v, n in PaymentReport.Status.choices
        ]
        return Response(options)

    @action(detail=False, methods=["get"], url_path="type-options")
    def type_options(self, request):
        """List available report type options"""
        options = [
            {"value": v, "display_name": n}
            for v, n in PaymentReport.ReportType.choices
        ]
        return Response(options)

    def list(self, request, *args, **kwargs):
        """Enhanced list with summary metadata"""
        response = super().list(request, *args, **kwargs)

        # Bila pagination response.data ni list - summary huwezekana tu kwenye dict
        if response.status_code == 200 and isinstance(response.data, dict):
            queryset = self.filter_queryset(self.get_queryset())
            response.data["summary"] = {
                "total_count": queryset.count(),
                "completed_count": queryset.filter(status=PaymentReport.Status.COMPLETED).count(),
                "generating_count": queryset.filter(status=PaymentReport.Status.GENERATING).count(),
                "failed_count": queryset.filter(status=PaymentReport.Status.FAILED).count(),
            }

        return response