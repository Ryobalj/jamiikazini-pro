# syllabus/views/lesson_plan_views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from syllabus.serializers.lesson_plan_serializers import (
    LessonPlanRequestSerializer,
    LessonPlanResponseSerializer,
)
from syllabus.services.lesson_plan_runtime_builder import LessonPlanRuntimeBuilder
from syllabus.services.academic_context import AcademicContext
from syllabus.models.teacher_workstation import TeacherWorkStation
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
            logger.info(f"Creating lesson plan for user: {user.username}")
            
            # Fetch user's active workstation
            try:
                workstation = TeacherWorkStation.objects.get(
                    teacher=user, 
                    is_active=True
                )
                logger.debug(f"Found workstation: {workstation.school_name}")
            except TeacherWorkStation.DoesNotExist:
                logger.error(f"No active workstation found for user: {user.username}")
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

    def create(self, request, *args, **kwargs):
        """
        Handle POST request to generate lesson plan.
        """
        try:
            logger.info(f"Lesson plan creation request from {request.user.username}")
            
            # Validate input
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Build lesson plan runtime data
            self.perform_create(serializer)
            lesson_plan = self.lesson_plan
            
            # 🔴 FIXED: Now lesson_plan has meta field, so serializer won't fail
            response_serializer = LessonPlanResponseSerializer(lesson_plan)
            
            logger.info(f"Successfully generated lesson plan for user: {request.user.username}")
            
            return Response(
                response_serializer.data,
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
        
        # Log internal server errors
        logger.error(f"Internal server error in lesson plan view: {str(exc)}", exc_info=True)
        
        return Response(
            {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while generating the lesson plan.",
                "details": str(exc) if getattr(self, 'settings', None) and self.settings.DEBUG else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )