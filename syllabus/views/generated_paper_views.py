# syllabus/views/generated_paper_views.py

import io
import zipfile
from datetime import datetime

from django.http import HttpResponse
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from syllabus.models.generated_paper import GeneratedPaper
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.timetable import TimeTable
from syllabus.permissions import CanDownloadPDF, FreeDownloadGateMixin
from syllabus.services.subscription_service import DownloadCategory
from syllabus.serializers.generated_paper_serializers import (
    GeneratePaperRequestSerializer,
    GeneratedPaperSerializer,
)
from syllabus.services.quiz_generation_service import build_custom_exam_format, generate_paper


def _verify_subject_in_timetable(user, subject_version) -> None:
    """Quiz/test/examination generation is topic-tree-driven content, same
    as Scheme of Work / Lesson Plan, so it's gated the same way: only for
    subjects the teacher actually has on their own timetable. Admins
    bypass, matching every other ownership check in this app."""
    if getattr(user, "role", None) == "ADMIN":
        return
    if not TimeTable.objects.filter(workstation__teacher=user, subject_version=subject_version).exists():
        raise ValidationError({
            "subject_version": "Somo hili halipo kwenye ratiba yako. Tafadhali liongeze kwenye ratiba yako kwanza."
        })


class GeneratedPaperViewSet(viewsets.ReadOnlyModelViewSet):
    """List/retrieve papers this teacher has already generated."""

    serializer_class = GeneratedPaperSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = GeneratedPaper.objects.select_related(
            "exam_format", "subject_version__subject", "subject_version__class_level", "workstation"
        ).prefetch_related("paper_questions__question")
        if getattr(user, "role", None) == "ADMIN":
            return qs
        return qs.filter(workstation__teacher=user)


class GeneratePaperAPIView(generics.CreateAPIView):
    """Randomly generate a new quiz/test/examination paper for the
    requesting teacher's own workstation and a subject on their own
    timetable. POST /syllabus/quiz/generate/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = GeneratePaperRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        workstation = TeacherWorkStation.objects.filter(teacher=request.user, is_active=True).first()
        if not workstation:
            raise ValidationError({"workstation": "Hujaweka kituo cha kazi bado."})

        subject_version = data["subject_version"]
        _verify_subject_in_timetable(request.user, subject_version)

        if data.get("exam_format"):
            exam_format = data["exam_format"]
            section_topic_ids = {
                str(scope["section"].id): [t.id for t in scope.get("topic_ids", [])]
                for scope in data.get("section_topics", [])
            }
        else:
            exam_format, section_topic_ids = build_custom_exam_format(
                workstation=workstation,
                paper_type=data["paper_type"],
                custom_sections=[
                    {
                        "name": section["name"],
                        "topic_ids": [t.id for t in section.get("topic_ids", [])],
                        "slots": section["slots"],
                    }
                    for section in data["custom_sections"]
                ],
                title=data.get("title", ""),
                time_allowed_minutes=data.get("time_allowed_minutes"),
                instructions=data.get("instructions", ""),
            )

        paper = generate_paper(
            exam_format=exam_format,
            subject_version=subject_version,
            workstation=workstation,
            section_topic_ids=section_topic_ids,
            title=data.get("title", ""),
            year=data.get("year"),
            term=data.get("term"),
        )
        return Response(GeneratedPaperSerializer(paper).data, status=status.HTTP_201_CREATED)


class GeneratedPaperPDFDownloadAPIView(FreeDownloadGateMixin, APIView):
    """Downloads a ZIP containing the blank question paper and the
    separate answer key / marking scheme, mirroring
    LessonPlanPDFDownloadAPIView's ZIP-of-two-PDFs pattern."""

    permission_classes = [IsAuthenticated, CanDownloadPDF]
    download_category = DownloadCategory.QUIZ_EXAM

    def get(self, request, pk=None):
        from syllabus.services.quiz_paper_pdf_builder import build_quiz_pdf
        from syllabus.services.quiz_answer_key_pdf_builder import build_quiz_answer_key_pdf

        try:
            paper = GeneratedPaper.objects.select_related(
                "exam_format", "subject_version__subject", "subject_version__class_level", "workstation"
            ).get(pk=pk)
        except GeneratedPaper.DoesNotExist:
            return Response({"detail": "Karatasi haikupatikana."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == "CLIENT" and paper.workstation.teacher != request.user:
            raise PermissionDenied("Huna ruhusa ya karatasi hii.")

        language = request.query_params.get("language", "sw")
        paper_bytes = build_quiz_pdf(paper, language=language, show_answers=False)
        key_bytes = build_quiz_answer_key_pdf(paper, language=language)

        subject_clean = paper.subject_version.subject.name.replace(" ", "_")
        class_clean = paper.subject_version.class_level.name.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        paper_name = f"Karatasi_{subject_clean}_{class_clean}_{timestamp}.pdf"
        key_name = f"Mwongozo_wa_Majibu_{subject_clean}_{class_clean}_{timestamp}.pdf"
        zip_name = f"{paper.exam_format.get_paper_type_display()}_{subject_clean}_{class_clean}_{timestamp}.zip"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(paper_name, paper_bytes)
            zf.writestr(key_name, key_bytes)

        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{zip_name}"'
        response["X-Filename"] = zip_name
        return response
