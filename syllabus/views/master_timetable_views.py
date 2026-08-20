# syllabus/views/master_timetable_views.py
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from syllabus.models.master_timetable import (
    MasterTimetableRoster,
    TimetablePeriodSlot,
    ActivityType,
    TimetableTeacher,
    TimetableTeacherAssignment,
    TimetableSlot,
)
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.serializers.master_timetable_serializers import (
    MasterTimetableRosterSerializer,
    TimetablePeriodSlotSerializer,
    ActivityTypeSerializer,
    TimetableTeacherSerializer,
    TimetableTeacherAssignmentSerializer,
    TimetableSlotSerializer,
)
from syllabus.permissions import IsAdminOrReadOnly, CanDownloadPDF
from syllabus.services.master_timetable_generator import MasterTimetableGenerator

# Default day layout matching the sample workbook this feature was built
# from: 9 real teaching periods + 2 named breaks - editable per roster
# after seeding via /seed-default-periods/.
DEFAULT_PERIODS = [
    dict(order=1, label="1", is_break=False),
    dict(order=2, label="2", is_break=False),
    dict(order=3, label="3", is_break=False),
    dict(order=4, label="MAPUMZIKO", is_break=True),
    dict(order=5, label="4", is_break=False),
    dict(order=6, label="5", is_break=False),
    dict(order=7, label="6", is_break=False),
    dict(order=8, label="MAPUMZIKO", is_break=True),
    dict(order=9, label="7", is_break=False),
    dict(order=10, label="8", is_break=False),
    dict(order=11, label="9", is_break=False),
]


class MasterTimetableRosterViewSet(viewsets.ModelViewSet):
    """Scoped strictly to the requesting teacher's own rosters - this
    subsystem is self-contained, not shared by school name like
    TimeTable's aggregation is (see plan: only the person who builds the
    roster views/exports it)."""
    serializer_class = MasterTimetableRosterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MasterTimetableRoster.objects.filter(
            owner__teacher=self.request.user
        ).select_related("owner")

    def perform_create(self, serializer):
        workstation = TeacherWorkStation.objects.filter(
            teacher=self.request.user, is_active=True
        ).first()
        if not workstation:
            raise PermissionDenied("Weka kituo cha kazi kwanza kabla ya kuunda ratiba kuu.")
        serializer.save(owner=workstation)

    @action(detail=True, methods=["post"], url_path="seed-default-periods")
    def seed_default_periods(self, request, pk=None):
        roster = self.get_object()
        if roster.period_slots.exists():
            return Response(
                {"detail": "Roster hii tayari ina muundo wa vipindi."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        slots = TimetablePeriodSlot.objects.bulk_create([
            TimetablePeriodSlot(roster=roster, **spec) for spec in DEFAULT_PERIODS
        ])
        serializer = TimetablePeriodSlotSerializer(slots, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        roster = self.get_object()
        result = MasterTimetableGenerator(roster).generate()
        return Response({
            "placed_count": result.placed_count,
            "is_complete": result.is_complete,
            "unplaced": [
                {
                    "teacher_name": u.teacher_name,
                    "subject_name": u.subject_name,
                    "class_level_name": u.class_level_name,
                    "periods_short": u.periods_short,
                }
                for u in result.unplaced
            ],
        })

    @action(detail=True, methods=["get"])
    def grid(self, request, pk=None):
        roster = self.get_object()
        slots = roster.slots.select_related(
            "period_slot", "class_level", "activity_type",
            "assignment", "assignment__teacher", "assignment__subject_version__subject",
        )

        teacher_id = request.query_params.get("teacher")
        class_level_id = request.query_params.get("class_level")
        if teacher_id:
            slots = slots.filter(assignment__teacher_id=teacher_id)
        if class_level_id:
            slots = slots.filter(class_level_id=class_level_id)

        serializer = TimetableSlotSerializer(slots, many=True)
        return Response(serializer.data)


class TimetablePeriodSlotViewSet(viewsets.ModelViewSet):
    serializer_class = TimetablePeriodSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TimetablePeriodSlot.objects.filter(
            roster__owner__teacher=self.request.user
        ).select_related("roster")


class ActivityTypeViewSet(viewsets.ModelViewSet):
    """Fixed built-in list, admin-managed reference data - read for any
    authenticated user (needed to populate slot-placement forms), write
    for Admin only. Mirrors ClassLevelViewSet's own convention."""
    queryset = ActivityType.objects.all().order_by("default_order", "code")
    serializer_class = ActivityTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class TimetableTeacherViewSet(viewsets.ModelViewSet):
    serializer_class = TimetableTeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TimetableTeacher.objects.filter(
            roster__owner__teacher=self.request.user
        ).select_related("roster", "workstation")


class TimetableTeacherAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = TimetableTeacherAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TimetableTeacherAssignment.objects.filter(
            roster__owner__teacher=self.request.user
        ).select_related(
            "roster", "teacher", "subject_version",
            "subject_version__subject", "subject_version__class_level",
        )


class TimetableSlotViewSet(viewsets.ModelViewSet):
    """Manual placement/editing of individual cells - e.g. whole-school
    activity blocks the roster owner places before running /generate/,
    or a hand-fixed cell afterward. Created here, rows always get
    source=MANUAL (see perform_create/update) - only the generator
    itself writes source=GENERATED rows."""
    serializer_class = TimetableSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TimetableSlot.objects.filter(
            roster__owner__teacher=self.request.user
        ).select_related(
            "roster", "period_slot", "class_level", "activity_type",
            "assignment", "assignment__teacher", "assignment__subject_version__subject",
        )

    def perform_create(self, serializer):
        serializer.save(source=TimetableSlot.Source.MANUAL)

    def perform_update(self, serializer):
        serializer.save(source=TimetableSlot.Source.MANUAL)


def _get_owned_roster(request, roster_id):
    return get_object_or_404(
        MasterTimetableRoster, id=roster_id, owner__teacher=request.user
    )


class MasterTimetablePDFAPIView(APIView):
    """Same subscription gate as every other document export in this
    app (CanDownloadPDF) - the master timetable is no exception."""
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def get(self, request, roster_id):
        from syllabus.services.master_timetable_pdf_builder import build_master_timetable_pdf

        roster = _get_owned_roster(request, roster_id)
        language = request.query_params.get("language", "sw")
        pdf_bytes = build_master_timetable_pdf(
            roster,
            language=language,
            teacher_id=request.query_params.get("teacher"),
            class_level_id=request.query_params.get("class_level"),
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = f"{roster.name.replace(' ', '_')}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class MasterTimetableXLSXAPIView(APIView):
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def get(self, request, roster_id):
        from syllabus.services.master_timetable_xlsx_builder import build_master_timetable_xlsx

        roster = _get_owned_roster(request, roster_id)
        language = request.query_params.get("language", "sw")
        xlsx_bytes = build_master_timetable_xlsx(
            roster,
            language=language,
            teacher_id=request.query_params.get("teacher"),
            class_level_id=request.query_params.get("class_level"),
        )
        response = HttpResponse(
            xlsx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        filename = f"{roster.name.replace(' ', '_')}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
