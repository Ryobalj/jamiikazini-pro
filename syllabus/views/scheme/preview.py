# syllabus/views/scheme/preview.py

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from syllabus.models import SubjectVersion
from syllabus.models.annual_calendar import AnnualCalendar
from syllabus.serializers.scheme_serializers import (
    SchemeRequestSerializer,
    SchemeResponseSerializer,
)
from syllabus.views.scheme_views import BaseSchemeService
from syllabus.permissions import IsAdminOrClientTeacher


class SchemePreviewAPIView(generics.CreateAPIView):
    """
    Preview Scheme (first 2 weeks only)
    """
    serializer_class = SchemeRequestSerializer
    permission_classes = [IsAuthenticated, IsAdminOrClientTeacher]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        subject_version = generics.get_object_or_404(
            SubjectVersion, id=data["subject_version_id"]
        )
        annual_calendar = generics.get_object_or_404(
            AnnualCalendar, id=data["annual_calendar_id"]
        )

        scheme = BaseSchemeService.build_scheme(
            subject_version,
            annual_calendar,
            request.user,
            data["balance_weekly"],
            data.get("language"),
        )

        result = SchemeResponseSerializer(scheme).data

        # 🔽 Limit to first 2 weeks
        weeks = {}
        for item in result.get("schedule_items", []):
            weeks.setdefault(item["week_number"], []).append(item)

        first_weeks = sorted(weeks.keys())[:2]
        limited = []
        for wk in first_weeks:
            limited.extend(weeks[wk])

        result["schedule_items"] = limited
        result["_preview"] = {
            "weeks_shown": len(first_weeks),
            "total_weeks": len(weeks),
            "note": "Preview only – full scheme available",
        }

        return Response(result, status=status.HTTP_200_OK)