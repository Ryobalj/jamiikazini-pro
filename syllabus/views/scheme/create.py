# syllabus/views/scheme/create.py

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
from datetime import datetime
import logging

from syllabus.models import SubjectVersion
from syllabus.models.annual_calendar import AnnualCalendar

from syllabus.serializers.scheme_serializers import (
    SchemeRequestSerializer,
    SchemeResponseSerializer,
)
from syllabus.views.scheme_views import BaseSchemeService
from syllabus.permissions import IsAdminOrClientTeacher, CanDownloadPDF
from syllabus.services.scheme_pdf_builder import SchemePDFBuilder
from syllabus.i18n import sw as sw_labels, en as en_labels

logger = logging.getLogger(__name__)


class SchemeCreateAPIView(generics.CreateAPIView):
    """
    Create Scheme of Work (JSON or PDF)
    POST /api/v1/syllabus/schemes/create/
    ?format=pdf
    """
    serializer_class = SchemeRequestSerializer
    permission_classes = [IsAuthenticated, IsAdminOrClientTeacher]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        subject_version = generics.get_object_or_404(
            SubjectVersion.objects.select_related(
                "subject", "class_level", "syllabus_version"
            ),
            id=data["subject_version_id"]
        )

        annual_calendar = generics.get_object_or_404(
            AnnualCalendar,
            id=data["annual_calendar_id"]
        )

        scheme = BaseSchemeService.build_scheme(
            subject_version=subject_version,
            annual_calendar=annual_calendar,
            user=request.user,
            balance_weekly=data["balance_weekly"],
            language=data.get("language"),
        )

        output_format = request.query_params.get("format", "json").lower()

        # ================= PDF =================
        if output_format == "pdf":
            if not CanDownloadPDF().has_permission(request, self):
                return Response(
                    {"detail": "PDF permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

            labels = (
                sw_labels.SCHEME_LABELS
                if scheme.identification.language == "sw"
                else en_labels.SCHEME_LABELS
            )

            pdf = SchemePDFBuilder(scheme, labels).build()
            filename = f"Scheme_{scheme.subject_name}_{datetime.now():%Y%m%d}.pdf"

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        # ================= JSON =================
        response_data = SchemeResponseSerializer(scheme).data
        response_data["_meta"] = {
            "generated_at": datetime.now().isoformat(),
            "syllabus_year": getattr(
                subject_version.syllabus_version, "year", None
            ),
            "is_current": getattr(
                subject_version.syllabus_version, "is_current", False
            ),
            "language": scheme.identification.language,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)