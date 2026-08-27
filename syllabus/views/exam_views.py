# syllabus/views/exam_views.py

from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.http import HttpResponse

from syllabus.models.student import Student
from syllabus.models.exam import Exam
from syllabus.models.mark import Mark
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.serializers.exam_serializers import (
    StudentSerializer, ExamSerializer, MarkSerializer, BulkMarkEntrySerializer,
)
from syllabus.services.exam_results_service import compute_class_results
from syllabus.permissions import CanDownloadPDF, FreeDownloadGateMixin


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["workstation", "class_level"]

    def get_queryset(self):
        user = self.request.user
        qs = Student.objects.all().select_related("workstation", "class_level")
        if user.role == "CLIENT":
            qs = qs.filter(workstation__teacher=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == "CLIENT":
            ws = serializer.validated_data.get("workstation")
            if ws and ws.teacher != user:
                raise PermissionDenied("Unaweza tu kutumia workstation yako mwenyewe.")
        serializer.save()


class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["workstation", "class_level"]

    def get_queryset(self):
        user = self.request.user
        qs = Exam.objects.all().select_related("workstation", "class_level").prefetch_related("subjects")
        if user.role == "CLIENT":
            qs = qs.filter(workstation__teacher=user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == "CLIENT":
            ws = serializer.validated_data.get("workstation")
            if ws and ws.teacher != user:
                raise PermissionDenied("Unaweza tu kutumia workstation yako mwenyewe.")
        serializer.save()

    @action(detail=True, methods=["get", "post"], url_path="marks")
    def marks(self, request, pk=None):
        exam = self.get_object()

        if request.method == "GET":
            marks = Mark.objects.filter(exam=exam).select_related("student", "subject")
            return Response(MarkSerializer(marks, many=True).data)

        entries_serializer = BulkMarkEntrySerializer(data=request.data, many=True)
        entries_serializer.is_valid(raise_exception=True)

        saved = []
        for entry in entries_serializer.validated_data:
            student = entry["student"]
            subject = entry["subject"]
            score = entry["score"]

            if student.workstation_id != exam.workstation_id or student.class_level_id != exam.class_level_id:
                raise ValidationError(f"Mwanafunzi {student.full_name} si wa darasa/kituo cha mtihani huu.")
            if not exam.subjects.filter(pk=subject.pk).exists():
                raise ValidationError(f"Somo {subject.name} halipo kwenye mtihani huu.")
            if score > exam.max_score_per_subject:
                raise ValidationError(
                    f"Alama za {student.full_name} kwa {subject.name} ({score}) "
                    f"zimezidi kiwango cha juu ({exam.max_score_per_subject})."
                )

            mark, _ = Mark.objects.update_or_create(
                exam=exam, student=student, subject=subject,
                defaults={"score": score},
            )
            saved.append(mark)

        return Response(MarkSerializer(saved, many=True).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="results")
    def results(self, request, pk=None):
        exam = self.get_object()
        results = compute_class_results(exam)
        data = {
            "subjects": [{"id": str(s.id), "name": s.name} for s in results["subjects"]],
            "students": [
                {
                    "student_id": str(r["student"].id),
                    "student_name": r["student"].full_name,
                    "gender": r["student"].gender,
                    "per_subject": {
                        str(subject_id): {
                            "score": entry["score"],
                            "grade": entry["grade"],
                            "rank": entry["rank"],
                        }
                        for subject_id, entry in r["per_subject"].items()
                    },
                    "total": r["total"],
                    "average": r["average"],
                    "overall_grade": r["overall_grade"],
                    "overall_rank": r["overall_rank"],
                }
                for r in results["students"]
            ],
        }
        return Response(data)


class ExamSubjectResultPDFAPIView(FreeDownloadGateMixin, APIView):
    """PDF ya matokeo ya somo moja tu, kwa mtihani fulani."""
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def get(self, request):
        from syllabus.services.exam_results_pdf_builder import build_subject_result_pdf
        from syllabus.models.subject import Subject

        exam = Exam.objects.filter(pk=request.query_params.get("exam_id")).first()
        subject = Subject.objects.filter(pk=request.query_params.get("subject_id")).first()
        if not exam or not subject:
            return Response({"detail": "Mtihani au somo halikupatikana."}, status=status.HTTP_404_NOT_FOUND)
        if request.user.role == "CLIENT" and exam.workstation.teacher != request.user:
            raise PermissionDenied("Huna ruhusa ya mtihani huu.")

        language = request.query_params.get("language", "sw")
        pdf_bytes = build_subject_result_pdf(exam, subject, language=language)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Matokeo_{subject.name}.pdf"'
        return response


class ExamClassReportPDFAPIView(FreeDownloadGateMixin, APIView):
    """PDF ya ripoti kamili ya darasa (masomo yote), kwa mtihani fulani."""
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def get(self, request):
        from syllabus.services.exam_results_pdf_builder import build_class_report_pdf

        exam = Exam.objects.filter(pk=request.query_params.get("exam_id")).first()
        if not exam:
            return Response({"detail": "Mtihani haukupatikana."}, status=status.HTTP_404_NOT_FOUND)
        if request.user.role == "CLIENT" and exam.workstation.teacher != request.user:
            raise PermissionDenied("Huna ruhusa ya mtihani huu.")

        language = request.query_params.get("language", "sw")
        pdf_bytes = build_class_report_pdf(exam, language=language)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Matokeo_{exam.class_level.name}.pdf"'
        return response


XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ExamSubjectResultXLSXAPIView(FreeDownloadGateMixin, APIView):
    """Excel (.xlsx) ya matokeo ya somo moja - thamani tu, hakuna formula."""
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def get(self, request):
        from syllabus.services.exam_results_xlsx_builder import build_subject_result_xlsx
        from syllabus.models.subject import Subject

        exam = Exam.objects.filter(pk=request.query_params.get("exam_id")).first()
        subject = Subject.objects.filter(pk=request.query_params.get("subject_id")).first()
        if not exam or not subject:
            return Response({"detail": "Mtihani au somo halikupatikana."}, status=status.HTTP_404_NOT_FOUND)
        if request.user.role == "CLIENT" and exam.workstation.teacher != request.user:
            raise PermissionDenied("Huna ruhusa ya mtihani huu.")

        language = request.query_params.get("language", "sw")
        xlsx_bytes = build_subject_result_xlsx(exam, subject, language=language)

        response = HttpResponse(xlsx_bytes, content_type=XLSX_CONTENT_TYPE)
        response["Content-Disposition"] = f'attachment; filename="Matokeo_{subject.name}.xlsx"'
        return response


class ExamClassReportXLSXAPIView(FreeDownloadGateMixin, APIView):
    """Excel (.xlsx) ya ripoti kamili ya darasa (masomo yote) - thamani tu, hakuna formula."""
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def get(self, request):
        from syllabus.services.exam_results_xlsx_builder import build_class_report_xlsx

        exam = Exam.objects.filter(pk=request.query_params.get("exam_id")).first()
        if not exam:
            return Response({"detail": "Mtihani haukupatikana."}, status=status.HTTP_404_NOT_FOUND)
        if request.user.role == "CLIENT" and exam.workstation.teacher != request.user:
            raise PermissionDenied("Huna ruhusa ya mtihani huu.")

        language = request.query_params.get("language", "sw")
        xlsx_bytes = build_class_report_xlsx(exam, language=language)

        response = HttpResponse(xlsx_bytes, content_type=XLSX_CONTENT_TYPE)
        response["Content-Disposition"] = f'attachment; filename="Matokeo_{exam.class_level.name}.xlsx"'
        return response
