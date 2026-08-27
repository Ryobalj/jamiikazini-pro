# syllabus/views/lesson_plan_views.py
from django.conf import settings as django_settings
from django.http import Http404, HttpResponse
from rest_framework import generics, status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from syllabus.serializers.lesson_plan_serializers import (
    LessonPlanRequestSerializer,
    LessonPlanResponseSerializer,
)
from syllabus.services.lesson_plan_runtime_builder import LessonPlanRuntimeBuilder
from syllabus.services.lesson_plan_pdf_builder import LessonPlanPDFBuilder
from syllabus.services.lesson_notes_pdf_builder import LessonNotesPDFBuilder
from syllabus.services.academic_context import AcademicContext
from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.permissions import CanDownloadPDF, FreeDownloadGateMixin
from syllabus.services.subscription_service import has_full_access, consume_free_download
from datetime import datetime
import io
import zipfile
import logging

logger = logging.getLogger(__name__)


class AutoLessonPlanCreateAPIView(generics.CreateAPIView):
    """
    Production-ready API endpoint to generate Lesson Plan automatically.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LessonPlanRequestSerializer

    def perform_create(self, serializer: LessonPlanRequestSerializer) -> None:
        """
        Build lesson plan runtime data using LessonPlanRuntimeBuilder.
        """
        try:
            user = self.request.user
            logger.info(f"Creating lesson plan for user: {user.email}")
            
            # Fetch user's active workstation
            try:
                workstation = TeacherWorkStation.objects.get(
                    teacher=user, 
                    is_active=True
                )
                logger.debug(f"Found workstation: {workstation.school_name}")
            except TeacherWorkStation.DoesNotExist:
                logger.error(f"No active workstation found for user: {user.email}")
                raise ValidationError({
                    "workstation": "Active teacher workstation not found. Please set up your workstation first."
                })
            
            # Extract validated data
            validated_data = serializer.validated_data
            timetable = validated_data["timetable"]
            specific_activity = validated_data["specific_activity"]
            date = validated_data["date"]
            
            # Log the request details
            logger.debug(f"Lesson plan request - Timetable: {timetable.id}, "
                        f"Activity: {specific_activity.id}, Date: {date}")
            
            # Create academic context
            academic_context = AcademicContext(
                workstation=workstation,
                timetable=timetable,
                subject_version=timetable.subject_version,
                date=date,
                period=validated_data.get("period"),
                timestart=validated_data.get("timestart"),
                timefinish=validated_data.get("timefinish"),
                boys_attended=validated_data.get("boys_attended"),
                girls_attended=validated_data.get("girls_attended"),
                language=validated_data.get("language"),
            )
            
            # Create lesson plan builder
            builder = LessonPlanRuntimeBuilder(
                specific_activity=specific_activity,
                academic_context=academic_context,
                date=date,
                period=validated_data.get("period") or timetable.period,
                start_time=validated_data.get("timestart") or timetable.timestart,
                end_time=validated_data.get("timefinish") or timetable.timefinish,
                registered_boys=timetable.registeredboys or 0,
                registered_girls=timetable.registeredgirls or 0,
                attended_boys=validated_data.get("boys_attended") or 0,
                attended_girls=validated_data.get("girls_attended") or 0,
                is_song=validated_data.get("is_song", False),
                managed_count=validated_data.get("managed_count"),
                repeat_next=validated_data.get("repeat_next", False),
            )
            
            self.lesson_plan = builder.build()
            logger.info(f"Successfully built lesson plan with {len(self.lesson_plan.lesson_steps)} steps")
            
        except Exception as e:
            logger.error(f"Error building lesson plan: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _apply_preview_truncation(lesson_plan):
        """
        Limit an unsubscribed teacher to ~25% of the generated content:
        only the first lesson step in full, and only the lesson notes
        introduction (no details/illustrations/daily-life examples or
        exercise questions) — enough to judge the tool, not enough to use
        it for free.
        """
        preview_step_count = max(1, round(len(lesson_plan.lesson_steps) * 0.25))
        lesson_plan.lesson_steps = lesson_plan.lesson_steps[:preview_step_count]

        lesson_plan.subject_info.lesson_notes_details = ""
        lesson_plan.subject_info.lesson_notes_illustrations = ""
        lesson_plan.subject_info.lesson_notes_daily_life = ""
        lesson_plan.subject_info.exercise_questions = []

        lesson_plan.reflection = None
        return lesson_plan

    def create(self, request, *args, **kwargs):
        """
        Handle POST request to generate lesson plan.
        """
        try:
            logger.info(f"Lesson plan creation request from {request.user.email}")
            
            # Validate input
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Build lesson plan runtime data
            self.perform_create(serializer)
            lesson_plan = self.lesson_plan

            # ====================
            # PDF FORMAT
            # ====================
            if request.query_params.get("format", "json").lower() == "pdf":
                logger.info("Generating PDF format...")
                if not CanDownloadPDF().has_permission(request, self):
                    return Response(
                        {"detail": "PDF download permission required."},
                        status=status.HTTP_403_FORBIDDEN
                    )

                language = lesson_plan.identification.language
                pdf_builder = LessonPlanPDFBuilder(data=lesson_plan, language=language)
                pdf_bytes = pdf_builder.build()

                class_clean = lesson_plan.identification.class_level.replace(" ", "_")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                if language == "sw":
                    filename = f"Andalio_la_Somo_{class_clean}_{timestamp}.pdf"
                else:
                    filename = f"Lesson_Plan_{class_clean}_{timestamp}.pdf"

                response = HttpResponse(pdf_bytes, content_type="application/pdf")
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
                response["X-Filename"] = filename
                response["X-Class-Level"] = lesson_plan.identification.class_level

                consume_free_download(request.user)
                logger.info(f"PDF generated: {filename}")
                return response

            # ====================
            # JSON FORMAT (DEFAULT)
            # ====================
            # Non-subscribers can generate and view a limited (~25%)
            # preview on-screen, but not the full content — full content
            # and PDF download both require CanDownloadPDF (active
            # subscription). See _apply_preview_truncation().
            is_full_access = has_full_access(request.user)
            if not is_full_access:
                lesson_plan = self._apply_preview_truncation(lesson_plan)

            # 🔴 FIXED: Now lesson_plan has meta field, so serializer won't fail
            response_serializer = LessonPlanResponseSerializer(lesson_plan)
            response_data = response_serializer.data
            response_data["_preview"] = {
                "is_preview": not is_full_access,
                "message": (
                    None if is_full_access else
                    "Muhtasari: unaonesha sehemu ndogo tu ya andalio (~25%). "
                    "Jiunge kwa usajili ili kuona na kupakua andalio kamili."
                ),
            }

            logger.info(f"Successfully generated lesson plan for user: {request.user.email}")

            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )
            
        except ValidationError as ve:
            # Log validation errors
            logger.warning(f"Validation error in lesson plan creation: {ve.detail}")
            raise
            
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in lesson plan creation: {str(e)}", exc_info=True)
            raise

    def handle_exception(self, exc):
        """
        Custom exception handling for better error responses.
        """
        if isinstance(exc, ValidationError):
            return Response(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Please check your input data",
                    "details": exc.detail,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Http404 (e.g. DRF's content negotiation rejecting an unknown
        # ?format=) and other recognized DRF exceptions (permission denied,
        # not authenticated, throttled, etc.) carry their own correct
        # status code - let DRF's default handling produce that instead of
        # masking every one of them as a generic 500 below.
        if isinstance(exc, (Http404, APIException)):
            return super().handle_exception(exc)

        # Log internal server errors
        logger.error(f"Internal server error in lesson plan view: {str(exc)}", exc_info=True)

        return Response(
            {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while generating the lesson plan.",
                # NOTE: `self.settings` on a DRF view is `rest_framework.settings.api_settings`,
                # not Django's settings - it has no DEBUG attribute, so the previous
                # `self.settings.DEBUG` check raised AttributeError here on every
                # non-ValidationError exception, crashing this handler itself and
                # surfacing a raw 500 traceback instead of the intended JSON error.
                "details": str(exc) if django_settings.DEBUG else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class LessonPlanPDFDownloadAPIView(FreeDownloadGateMixin, generics.CreateAPIView):
    """
    Download endpoint for Andalio la Somo — returns a ZIP containing TWO
    separate PDFs: the Andalio la Somo (lesson plan) itself and a
    standalone Nukuu za Somo (lesson notes + exercise) document. They're
    deliberately kept as two documents rather than merged into one PDF,
    but bundled into a single download so the teacher gets both from one
    click.

    DRF's default content negotiation treats `?format=` as a reserved
    override for renderer selection and raises Http404 for any value that
    isn't a registered renderer (e.g. "pdf") *before* create() ever runs.
    Hitting AutoLessonPlanCreateAPIView directly with `?format=pdf` would
    therefore 404. This view sidesteps DRF's URL-routed dispatch/content
    negotiation entirely and calls create() directly, mirroring
    SchemePDFDownloadAPIView in scheme_views.py.
    """
    permission_classes = [IsAuthenticated, CanDownloadPDF]
    serializer_class = LessonPlanRequestSerializer

    def create(self, request, *args, **kwargs):
        # Note: deliberately not proxying to AutoLessonPlanCreateAPIView via
        # a deep-copied request (as the analogous SchemePDFDownloadAPIView
        # in scheme_views.py does) — a real, already-routed Django request
        # carries a `resolver_match` attribute that isn't picklable, so
        # copy.deepcopy(request) raises "Cannot pickle ResolverMatch" on
        # any real HTTP call. Building the PDF directly here avoids that.
        try:
            logger.info(f"PDF download request from user: {request.user.email}")

            main_view = AutoLessonPlanCreateAPIView()
            main_view.request = request
            main_view.format_kwarg = None

            serializer = main_view.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            main_view.perform_create(serializer)
            lesson_plan = main_view.lesson_plan

            language = lesson_plan.identification.language
            andalio_bytes = LessonPlanPDFBuilder(data=lesson_plan, language=language).build()
            notes_bytes = LessonNotesPDFBuilder(data=lesson_plan, language=language).build()

            class_clean = lesson_plan.identification.class_level.replace(" ", "_")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            if language == "sw":
                andalio_name = f"Andalio_la_Somo_{class_clean}_{timestamp}.pdf"
                notes_name = f"Nukuu_za_Somo_{class_clean}_{timestamp}.pdf"
                zip_name = f"Andalio_na_Nukuu_{class_clean}_{timestamp}.zip"
            else:
                andalio_name = f"Lesson_Plan_{class_clean}_{timestamp}.pdf"
                notes_name = f"Lesson_Notes_{class_clean}_{timestamp}.pdf"
                zip_name = f"Lesson_Plan_and_Notes_{class_clean}_{timestamp}.zip"

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(andalio_name, andalio_bytes)
                zf.writestr(notes_name, notes_bytes)
            zip_bytes = zip_buffer.getvalue()

            response = HttpResponse(zip_bytes, content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="{zip_name}"'
            response["X-Filename"] = zip_name
            response["X-Class-Level"] = lesson_plan.identification.class_level

            logger.info(f"Lesson plan ZIP generated: {zip_name} ({andalio_name} + {notes_name})")
            return response

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"PDF download failed: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to generate PDF.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )