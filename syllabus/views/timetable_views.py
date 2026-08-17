# syllabus/views/timetable_views.py

from rest_framework import viewsets, filters, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.http import HttpResponse

from syllabus.models.timetable import TimeTable
from syllabus.serializers.timetable_serializer import TimeTableSerializer
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.permissions import CanDownloadPDF

class TimeTableViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for TimeTable
    """
    serializer_class = TimeTableSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "workstation__teacher__full_name",
        "subject_version__subject__name",
        "subject_version__class_level__name"
    ]
    ordering_fields = ["period", "timestart", "timefinish"]
    ordering = ["period"]

    def get_queryset(self):
        user = self.request.user
        # Always scope to the logged-in teacher's own timetable, regardless
        # of role - the earlier "only if CLIENT" check let any other role
        # (e.g. ADMIN) see every teacher's classes/subjects unfiltered,
        # which defeats lesson-plan/scheme tooling that assumes "my
        # timetable" means the logged-in teacher's own schedule.
        return TimeTable.objects.filter(workstation__teacher=user).select_related(
            "workstation",
            "subject_version",
            "subject_version__subject",
            "subject_version__class_level",
            "subject_version__syllabus_version"
        )

    def perform_create(self, serializer):
        user = self.request.user
        # Hakikisha mwalimu anatumia workstation yake tu
        if user.role == "CLIENT":
            ws = serializer.validated_data.get('workstation')
            if ws and ws.teacher != user:
                raise PermissionDenied("Unaweza tu kutumia workstation yako mwenyewe.")
        serializer.save()


class TeacherTimetablePDFAPIView(APIView):
    """PDF ya ratiba ya kibinafsi ya mwalimu aliyeingia (kutoka workstation yake)."""
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def get(self, request):
        from syllabus.services.timetable_pdf_builder import build_teacher_timetable_pdf

        workstation = TeacherWorkStation.objects.filter(teacher=request.user, is_active=True).first()
        if not workstation:
            return Response({"detail": "Hujaweka kituo cha kazi bado."}, status=status.HTTP_404_NOT_FOUND)

        language = request.query_params.get("language", "sw")
        pdf_bytes = build_teacher_timetable_pdf(workstation, language=language)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Ratiba_{workstation.teacher.username}.pdf"'
        return response


class SchoolTimetablePDFAPIView(APIView):
    """PDF ya ratiba kuu ya shule nzima, ikijumuisha vipindi vya walimu wote
    wenye workstation shuleni humo. Admin anaweza kuchagua shule kwa
    ?school_name=; mwalimu wa kawaida hupata shule ya workstation yake."""
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def get(self, request):
        from syllabus.services.school_timetable_pdf_builder import build_school_timetable_pdf

        school_name = request.query_params.get("school_name")
        if not school_name:
            workstation = TeacherWorkStation.objects.filter(teacher=request.user, is_active=True).first()
            if not workstation:
                return Response({"detail": "Hujaweka kituo cha kazi bado."}, status=status.HTTP_404_NOT_FOUND)
            school_name = workstation.school_name

        language = request.query_params.get("language", "sw")
        pdf_bytes = build_school_timetable_pdf(school_name, language=language)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Ratiba_Kuu_{school_name}.pdf"'
        return response


XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class TeacherTimetableXLSXAPIView(APIView):
    """Excel (.xlsx) ya ratiba ya kibinafsi ya mwalimu - thamani tu, hakuna formula."""
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def get(self, request):
        from syllabus.services.timetable_xlsx_builder import build_teacher_timetable_xlsx

        workstation = TeacherWorkStation.objects.filter(teacher=request.user, is_active=True).first()
        if not workstation:
            return Response({"detail": "Hujaweka kituo cha kazi bado."}, status=status.HTTP_404_NOT_FOUND)

        language = request.query_params.get("language", "sw")
        xlsx_bytes = build_teacher_timetable_xlsx(workstation, language=language)

        response = HttpResponse(xlsx_bytes, content_type=XLSX_CONTENT_TYPE)
        response["Content-Disposition"] = f'attachment; filename="Ratiba_{workstation.teacher.username}.xlsx"'
        return response


class SchoolTimetableXLSXAPIView(APIView):
    """Excel (.xlsx) ya ratiba kuu ya shule nzima - thamani tu, hakuna formula."""
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def get(self, request):
        from syllabus.services.timetable_xlsx_builder import build_school_timetable_xlsx

        school_name = request.query_params.get("school_name")
        if not school_name:
            workstation = TeacherWorkStation.objects.filter(teacher=request.user, is_active=True).first()
            if not workstation:
                return Response({"detail": "Hujaweka kituo cha kazi bado."}, status=status.HTTP_404_NOT_FOUND)
            school_name = workstation.school_name

        language = request.query_params.get("language", "sw")
        xlsx_bytes = build_school_timetable_xlsx(school_name, language=language)

        response = HttpResponse(xlsx_bytes, content_type=XLSX_CONTENT_TYPE)
        response["Content-Disposition"] = f'attachment; filename="Ratiba_Kuu_{school_name}.xlsx"'
        return response
