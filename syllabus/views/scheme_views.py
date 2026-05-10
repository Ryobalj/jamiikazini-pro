# syllabus/views/scheme_views.py

from typing import Any, Dict, Optional, List
from django.http import HttpResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
import logging
import uuid

from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.annual_calendar import AnnualCalendar
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.serializers.scheme_serializers import (
    SchemeRequestSerializer,
    SchemeResponseSerializer,
)
from syllabus.services.scheme_timeline_builder import SchemeTimelineBuilder
from syllabus.services.scheme_pdf_builder import SchemePDFBuilder
from syllabus.permissions import CanDownloadPDF, IsAdminOrClientTeacher
from syllabus.services.competence_tree_service import CompetenceTreeService
from syllabus.services.calendar_service import CalendarService
from syllabus.i18n import sw as sw_labels, en as en_labels
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseSchemeService:
    """Base service with common scheme building logic."""
    
    @staticmethod
    def validate_and_get_ids(data: Dict) -> tuple:
        """Validate and extract UUIDs from request data."""
        subject_version_id = data.get("subject_version_id")
        calendar_id = data.get("annual_calendar_id")
        
        if not subject_version_id or not calendar_id:
            raise ValidationError({
                "detail": "Both subject_version_id and annual_calendar_id are required."
            })
        
        try:
            return (
                uuid.UUID(str(subject_version_id)),
                uuid.UUID(str(calendar_id))
            )
        except (ValueError, AttributeError, TypeError):
            raise ValidationError({
                "detail": "Invalid ID format. Please provide valid UUIDs.",
                "subject_version_id": "Must be a valid UUID format like: 2a921410-196e-475e-ae97-bf2690d2c2de",
                "annual_calendar_id": "Must be a valid UUID format"
            })
    
    @staticmethod
    def get_teacher_info(user) -> Dict:
        """Get teacher information."""
        try:
            workstation = TeacherWorkStation.objects.filter(
                teacher=user,
                is_active=True
            ).first()
            
            if workstation:
                return {
                    "teacher_name": user.get_full_name() or user.username,
                    "school_name": getattr(workstation, "school_name", "School"),
                    "council": getattr(workstation, "district", ""),
                    "ward": getattr(workstation, "ward", ""),
                    "region": getattr(workstation, "region", ""),
                    "workstation_id": workstation.id,
                }
        except Exception as e:
            logger.warning(f"Could not get workstation: {str(e)}")
        
        # Fallback if no workstation
        return {
            "teacher_name": user.get_full_name() or user.username,
            "school_name": "School",
            "council": "",
            "ward": "",
            "region": "",
            "workstation_id": None,
        }
    
    @staticmethod
    def get_subject_info(subject_version: SubjectVersion, 
                        annual_calendar: AnnualCalendar,
                        language: str) -> Dict:
        """Get subject information."""
        # Language selection
        labels = sw_labels.SCHEME_LABELS if language == "sw" else en_labels.SCHEME_LABELS
        
        # Get objectives from main competences
        objectives = []
        try:
            if hasattr(subject_version, 'main_competences'):
                # Get first 3 main competences for objectives
                main_competences = subject_version.main_competences.all()[:3]
                for comp in main_competences:
                    objectives.append(comp.description or comp.name)
        except Exception as e:
            logger.warning(f"Could not get objectives: {str(e)}")
        
        if not objectives:
            subject_name = getattr(subject_version.subject, 'name', 'Subject')
            objectives = [f"Kujifunza {subject_name}"]
        
        # Get periods per week from Subject model
        periods_per_week = 1  # Default
        try:
            if hasattr(subject_version.subject, 'periods_per_week'):
                periods_per_week = subject_version.subject.periods_per_week or periods_per_week
        except:
            pass
        
        # Get class level display name
        class_level_name = subject_version.class_level.name
        if hasattr(subject_version.class_level, 'display_name'):
            class_level_name = subject_version.class_level.display_name
        
        # Get syllabus year
        syllabus_year = ""
        try:
            if hasattr(subject_version, 'syllabus_version') and subject_version.syllabus_version:
                syllabus_year = subject_version.syllabus_version.year
        except:
            pass
        
        return {
            "subject_name": subject_version.subject.name,
            "class_level": subject_version.class_level.name,
            "class_level_name": class_level_name,
            "year": str(annual_calendar.year),
            "syllabus_year": str(syllabus_year),
            "academic_year": f"{annual_calendar.year}/{annual_calendar.year + 1}",
            "term": "I & II",  # Full academic year
            "term_display": "Muhula wa I & II" if language == "sw" else "Term I & II",
            "objectives": objectives,
            "headers": labels.get("headers", []),
            "periods_per_week": periods_per_week,
            "total_periods": 0,  # Will be calculated by builder
            "language": language,
            "is_english": getattr(subject_version, 'is_english', False),
            "is_awali": getattr(subject_version, 'is_awali', False),
        }
    
    @staticmethod
    def _extract_activities_from_subject_version(subject_version: SubjectVersion) -> List[Dict]:
        """Extract activities directly from SubjectVersion in SchemeTimelineBuilder format."""
        activities = []
        activity_index = 0
        
        try:
            logger.info(f"Extracting activities from subject version: {subject_version.id}")
            
            # Get main competences in order
            main_competences = subject_version.main_competences.all().order_by('order')
            
            if not main_competences.exists():
                logger.warning(f"No main competences found for subject version: {subject_version.id}")
                return activities
            
            for main_idx, main_comp in enumerate(main_competences):
                # Get specific competences in order
                specific_competences = main_comp.specific_competences.all().order_by('order')
                
                for sp_idx, spec_comp in enumerate(specific_competences):
                    # Get learning activities in order
                    learning_activities = spec_comp.learning_activities.all().order_by('order')
                    
                    for la_idx, learn_act in enumerate(learning_activities):
                        # Get specific learning activities in order
                        specific_activities = learn_act.specific_activities.all().order_by('order')
                        
                        for sa_idx, spec_act in enumerate(specific_activities):
                            activity_index += 1
                            
                            activity = {
                                "index": activity_index,
                                "main_competence": main_comp.name,
                                "main_order": main_comp.order,
                                "specific_competence": spec_comp.name,
                                "specific_order": spec_comp.order,
                                "learning_activity": learn_act.name,
                                "learning_order": learn_act.order,
                                "specific_learning": spec_act.name,
                                "specific_learning_order": spec_act.order,
                                "periods_needed": spec_act.periods or 1,
                                "method": spec_act.method or "Majadiliano na mazoezi",
                                "assessment_criteria": spec_act.assessment_criteria or "Ushiriki na mazoezi",
                                "teaching_aids": spec_act.teaching_aids or "Kadi, chati, kitabu",
                                "references": spec_act.references or "Kitabu cha mwanafunzi",
                            }
                            
                            activities.append(activity)
            
            logger.info(f"✅ Extracted {len(activities)} activities from subject version")
            
            # Calculate cumulative periods
            cumulative = 0
            for activity in activities:
                cumulative += activity["periods_needed"]
                activity["cumulative_periods"] = cumulative
            
            return activities
            
        except Exception as e:
            logger.error(f"❌ Error extracting activities: {str(e)}", exc_info=True)
            return []
    
    @classmethod
    def build_scheme(cls, 
                    subject_version: SubjectVersion,
                    annual_calendar: AnnualCalendar,
                    user,
                    balance_weekly: bool = True,
                    language: Optional[str] = None) -> Any:
        """Build a scheme from models using SchemeTimelineBuilder."""
        try:
            # Determine language
            if language and language in ["sw", "en"]:
                lang = language
            else:
                lang = "en" if getattr(subject_version, "is_english", False) else "sw"
            
            logger.info(f"📋 Building scheme in {lang} language")
            
            # Get contexts
            teacher_info = cls.get_teacher_info(user)
            subject_info = cls.get_subject_info(subject_version, annual_calendar, lang)
            
            # Extract activities from subject version
            logger.info(f"🔍 Extracting activities for: {subject_version.subject.name}")
            activities = cls._extract_activities_from_subject_version(subject_version)
            
            if not activities:
                raise ValidationError({
                    "detail": "No learning activities found for this subject version. "
                              "Please check if this subject has specific learning activities defined."
                })
            
            # Create competence tree structure expected by SchemeTimelineBuilder
            competence_tree = {
                "subject_version_id": str(subject_version.id),
                "subject_name": subject_version.subject.name,
                "class_level": subject_version.class_level.name,
                "activities": activities,
                "competences": []  # Empty for now, activities are the main data
            }
            
            # Initialize calendar service
            calendar_service = CalendarService(annual_calendar)
            
            # Create and execute builder
            logger.info("🚀 Creating SchemeTimelineBuilder...")
            builder = SchemeTimelineBuilder(
                competence_tree=competence_tree,
                calendar_service=calendar_service,
                teacher_info=teacher_info,
                subject_info=subject_info,
            )
            
            # Build scheme
            logger.info("🏗️  Building scheme...")
            scheme = builder.build(balance_weekly=balance_weekly)
            
            # Get statistics
            stats = builder.get_statistics()
            
            logger.info(f"✅ Scheme built successfully: {subject_version.subject.name} - "
                       f"Language: {lang}, Activities: {len(activities)}, "
                       f"Study Weeks: {stats.get('study_weeks', 0)}, "
                       f"Total Periods: {stats.get('total_periods_needed', 0)}")
            
            return scheme
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Error building scheme: {str(e)}", exc_info=True)
            raise ValidationError({
                "detail": f"Failed to build scheme: {str(e)}"
            })


class SchemeCreateAPIView(generics.CreateAPIView):
    """
    Create a scheme of work.
    
    Supports ALL syllabus versions (current and old).
    
    POST /api/schemes/create/
    {
        "subject_version_id": "uuid",
        "annual_calendar_id": "uuid",
        "balance_weekly": true,
        "language": "sw"
    }
    
    Query param: ?format=pdf for PDF download
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrClientTeacher]
    serializer_class = SchemeRequestSerializer
    parser_classes = [JSONParser]
    
    def create(self, request, *args, **kwargs):
        """Handle scheme creation."""
        logger.info(f"📝 Scheme creation request from user: {request.user.username}")
        
        try:
            # Parse request data
            data = request.data
            logger.debug(f"Request data: {data}")
            
            # Manual validation first
            subject_version_id = data.get("subject_version_id")
            calendar_id = data.get("annual_calendar_id")
            
            if not subject_version_id:
                return Response(
                    {"detail": "subject_version_id is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not calendar_id:
                return Response(
                    {"detail": "annual_calendar_id is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert to UUID
            try:
                subject_version_uuid = uuid.UUID(str(subject_version_id))
                calendar_uuid = uuid.UUID(str(calendar_id))
            except (ValueError, AttributeError, TypeError) as e:
                logger.error(f"❌ Invalid UUID format: {str(e)}")
                return Response(
                    {
                        "detail": "Invalid ID format.",
                        "subject_version_id": "Must be a valid UUID like: 12345678-1234-1234-1234-123456789abc",
                        "annual_calendar_id": "Must be a valid UUID"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get subject version with related data
            logger.info(f"🔍 Looking for SubjectVersion: {subject_version_uuid}")
            try:
                subject_version = SubjectVersion.objects.select_related(
                    'subject', 
                    'class_level',
                    'syllabus_version'
                ).get(id=subject_version_uuid)
                
                # Log syllabus info
                syllabus_info = "No syllabus"
                if subject_version.syllabus_version:
                    syllabus_info = f"{subject_version.syllabus_version.year} (current: {subject_version.syllabus_version.is_current})"
                
                logger.info(f"✅ Found SubjectVersion: {subject_version.subject.name} - "
                          f"Class: {subject_version.class_level.name} - "
                          f"Syllabus: {syllabus_info} - "
                          f"English: {getattr(subject_version, 'is_english', False)} - "
                          f"Awali: {getattr(subject_version, 'is_awali', False)}")
                
            except SubjectVersion.DoesNotExist:
                logger.error(f"❌ SubjectVersion not found: {subject_version_uuid}")
                return Response(
                    {"detail": f"Subject version with ID {subject_version_id} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get annual calendar
            logger.info(f"🔍 Looking for AnnualCalendar: {calendar_uuid}")
            try:
                annual_calendar = AnnualCalendar.objects.get(id=calendar_uuid)
                logger.info(f"✅ Found AnnualCalendar: {annual_calendar.institute} - {annual_calendar.year}")
            except AnnualCalendar.DoesNotExist:
                logger.error(f"❌ AnnualCalendar not found: {calendar_uuid}")
                return Response(
                    {"detail": f"Annual calendar with ID {calendar_id} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Extract other parameters
            balance_weekly = data.get("balance_weekly", True)
            language = data.get("language")
            
            # Log syllabus status (for information only, not for restriction)
            if subject_version.syllabus_version:
                logger.info(f"📚 Syllabus Version Status: {subject_version.syllabus_version.year} - "
                          f"Current: {subject_version.syllabus_version.is_current}")
            
            # Build scheme
            logger.info("🚀 Starting scheme building...")
            scheme = BaseSchemeService.build_scheme(
                subject_version=subject_version,
                annual_calendar=annual_calendar,
                user=request.user,
                balance_weekly=balance_weekly,
                language=language
            )
            
            # Check format
            output_format = request.query_params.get("format", "json").lower()
            
            # ====================
            # PDF FORMAT
            # ====================
            if output_format == "pdf":
                logger.info("📄 Generating PDF format...")
                # Check permission
                if not CanDownloadPDF().has_permission(request, self):
                    return Response(
                        {"detail": "PDF download permission required."},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Generate PDF
                labels = sw_labels.SCHEME_LABELS if scheme.identification.language == "sw" else en_labels.SCHEME_LABELS
                pdf_builder = SchemePDFBuilder(data=scheme, labels=labels)
                pdf_bytes = pdf_builder.build()
                
                # Create filename
                subject_clean = scheme.subject_name.replace(" ", "_")
                class_clean = scheme.class_level_name.replace(" ", "_")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                
                if scheme.identification.language == "sw":
                    filename = f"Azimio_la_Kazi_{subject_clean}_{class_clean}_{timestamp}.pdf"
                else:
                    filename = f"Scheme_of_Work_{subject_clean}_{class_clean}_{timestamp}.pdf"
                
                # Create response
                response = HttpResponse(pdf_bytes, content_type="application/pdf")
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
                response["X-Filename"] = filename
                response["X-Subject"] = scheme.subject_name
                response["X-Class-Level"] = scheme.class_level_name
                response["X-Syllabus-Year"] = getattr(scheme, 'syllabus_year', annual_calendar.year)
                
                logger.info(f"✅ PDF generated: {filename}")
                return response
            
            # ====================
            # JSON FORMAT (DEFAULT)
            # ====================
            logger.info("📋 Generating JSON format...")
            response_serializer = SchemeResponseSerializer(scheme)
            response_data = response_serializer.data
            
            # Calculate statistics
            schedule_items = response_data.get("schedule_items", [])
            total_weeks = len(set(item.get("week_number", 0) for item in schedule_items))
            total_periods = sum(item.get("periods", 0) for item in schedule_items)
            
            # Add metadata
            response_data["_meta"] = {
                "generated_at": datetime.now().isoformat(),
                "format": "json",
                "language": scheme.identification.language,
                "periods_per_week": getattr(scheme, 'periods_per_week', 1),
                "total_weeks": total_weeks,
                "total_periods": total_periods,
                "syllabus_year": getattr(subject_version.syllabus_version, 'year', 'N/A') if subject_version.syllabus_version else 'N/A',
                "syllabus_is_current": getattr(subject_version.syllabus_version, 'is_current', False) if subject_version.syllabus_version else False,
                "note": "Scheme generated successfully. All syllabus versions are supported."
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            logger.error(f"❌ Validation error: {str(e)}")
            error_detail = e.detail if hasattr(e, 'detail') else str(e)
            return Response(
                {"detail": error_detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"❌ Unexpected error creating scheme: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"Failed to create scheme: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SchemePreviewAPIView(generics.CreateAPIView):
    """
    Preview a scheme before final generation.
    
    Supports ALL syllabus versions (current and old).
    
    Returns limited data (first 2 weeks) for review.
    
    POST /api/schemes/preview/
    {
        "subject_version_id": "uuid",
        "annual_calendar_id": "uuid",
        "balance_weekly": true,
        "language": "sw"
    }
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrClientTeacher]
    
    def post(self, request, *args, **kwargs):
        """Generate scheme preview."""
        logger.info(f"👁️  Scheme preview request from user: {request.user.username}")
        
        try:
            data = request.data
            logger.debug(f"Preview request data: {data}")
            
            # Validate required fields
            subject_version_id = data.get("subject_version_id")
            calendar_id = data.get("annual_calendar_id")
            
            if not subject_version_id:
                return Response(
                    {"detail": "subject_version_id is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not calendar_id:
                return Response(
                    {"detail": "annual_calendar_id is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert to UUID
            try:
                subject_version_uuid = uuid.UUID(str(subject_version_id))
                calendar_uuid = uuid.UUID(str(calendar_id))
            except (ValueError, AttributeError, TypeError) as e:
                logger.error(f"❌ Invalid UUID format in preview: {str(e)}")
                return Response(
                    {"detail": "Invalid ID format. Please provide valid UUIDs."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get models
            try:
                subject_version = SubjectVersion.objects.select_related(
                    'subject', 'class_level', 'syllabus_version'
                ).get(id=subject_version_uuid)
                
                logger.info(f"👁️  Preview - Found subject: {subject_version.subject.name} - "
                          f"Class: {subject_version.class_level.name} - "
                          f"Syllabus: {getattr(subject_version.syllabus_version, 'year', 'N/A')}")
                
            except SubjectVersion.DoesNotExist:
                return Response(
                    {"detail": f"Subject version not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            try:
                annual_calendar = AnnualCalendar.objects.get(id=calendar_uuid)
            except AnnualCalendar.DoesNotExist:
                return Response(
                    {"detail": f"Annual calendar not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Build scheme
            scheme = BaseSchemeService.build_scheme(
                subject_version=subject_version,
                annual_calendar=annual_calendar,
                user=request.user,
                balance_weekly=data.get("balance_weekly", True),
                language=data.get("language")
            )
            
            # Convert to response
            response_serializer = SchemeResponseSerializer(scheme)
            preview_data = response_serializer.data
            
            # ====================
            # LIMIT DATA FOR PREVIEW
            # ====================
            if "schedule_items" in preview_data and preview_data["schedule_items"]:
                # Get unique weeks
                weeks = {}
                for item in preview_data["schedule_items"]:
                    week_num = item.get("week_number", 0)
                    if week_num not in weeks:
                        weeks[week_num] = []
                    weeks[week_num].append(item)
                
                # Show only first 2 weeks for preview
                sorted_weeks = sorted(weeks.keys())
                preview_weeks = sorted_weeks[:2] if sorted_weeks else []
                limited_items = []
                for week in preview_weeks:
                    limited_items.extend(weeks[week])
                
                preview_data["schedule_items"] = limited_items
                
                # Add week statistics
                total_weeks = len(weeks)
                preview_weeks_count = len(preview_weeks)
            else:
                total_weeks = 0
                preview_weeks_count = 0
            
            # ====================
            # ADD PREVIEW METADATA
            # ====================
            syllabus_info = {}
            if subject_version.syllabus_version:
                syllabus_info = {
                    "year": subject_version.syllabus_version.year,
                    "is_current": subject_version.syllabus_version.is_current,
                    "note": "All syllabus versions are supported"
                }
            
            preview_data["_preview"] = {
                "is_preview": True,
                "subject": subject_version.subject.name,
                "class_level": subject_version.class_level.name,
                "teacher": request.user.get_full_name() or request.user.username,
                "calendar_year": annual_calendar.year,
                "syllabus_info": syllabus_info,
                "total_weeks": total_weeks,
                "preview_weeks": preview_weeks_count,
                "message": f"Preview showing first {preview_weeks_count} of {total_weeks} weeks.",
                "generated_at": datetime.now().isoformat(),
                "full_scheme_available": True,
                "pdf_available": CanDownloadPDF().has_permission(request, self),
                "syllabus_support": "ALL versions supported (current and historical)",
                "next_steps": {
                    "get_full_json": f"/api/schemes/create/",
                    "get_pdf": f"/api/schemes/create/?format=pdf",
                    "note": "Use the same parameters for full scheme generation"
                }
            }
            
            # Add basic info at top level for easy access
            preview_data["basic_info"] = {
                "subject": subject_version.subject.name,
                "class": subject_version.class_level.name,
                "teacher": request.user.get_full_name() or request.user.username,
                "year": annual_calendar.year,
                "syllabus_year": subject_version.syllabus_version.year if subject_version.syllabus_version else "N/A",
                "language": scheme.identification.language if hasattr(scheme, 'identification') else "sw",
                "syllabus_status": "current" if (subject_version.syllabus_version and subject_version.syllabus_version.is_current) else "historical"
            }
            
            return Response(preview_data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"❌ Error generating preview: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"Failed to generate preview: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SchemePDFDownloadAPIView(generics.CreateAPIView):
    """
    PDF download endpoint.
    Reuses SchemeCreateAPIView but forces PDF output.
    """
    permission_classes = [IsAuthenticated, CanDownloadPDF]
    serializer_class = SchemeRequestSerializer

    def create(self, request, *args, **kwargs):
        """
        Generate and download PDF safely.
        """
        import copy
        from rest_framework.response import Response
        from rest_framework import status

        try:
            logger.info(f"📄 PDF download request from user: {request.user.username}")
            
            # Copy the request so we don't modify the original
            pdf_request = copy.deepcopy(request)
            pdf_request.method = 'POST'

            # Add format=pdf to query parameters
            if hasattr(pdf_request, 'query_params'):
                pdf_request.query_params = pdf_request.query_params.copy()
                pdf_request.query_params['format'] = 'pdf'
            else:
                pdf_request.GET = pdf_request.GET.copy()
                pdf_request.GET['format'] = 'pdf'

            # Call the main create view
            main_view = SchemeCreateAPIView()
            main_view.request = pdf_request
            main_view.format_kwarg = None

            # Call create and return its response
            logger.info("🔧 Calling main SchemeCreateAPIView for PDF generation...")
            return main_view.create(pdf_request, *args, **kwargs)

        except Exception as e:
            logger.error(f"❌ PDF download failed: {str(e)}", exc_info=True)
            return Response(
                {
                    "detail": "Failed to generate PDF.",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# SIMPLE DEBUG ENDPOINT
# ============================================

from rest_framework.views import APIView

class SchemeDebugAPIView(APIView):
    """Debug endpoint to check scheme parameters."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Check if IDs exist and return basic info."""
        try:
            data = request.data
            
            # Check IDs
            subject_version_id = data.get("subject_version_id")
            calendar_id = data.get("annual_calendar_id")
            
            result = {
                "request_data": data,
                "user": request.user.username,
                "checks": {},
                "message": "Debug check - ALL syllabus versions are supported"
            }
            
            # Check subject version
            if subject_version_id:
                try:
                    subject_uuid = uuid.UUID(str(subject_version_id))
                    subject_version = SubjectVersion.objects.select_related(
                        'subject', 'class_level', 'syllabus_version'
                    ).get(id=subject_uuid)
                    
                    # Check syllabus info
                    syllabus_info = {}
                    if subject_version.syllabus_version:
                        syllabus_info = {
                            "year": subject_version.syllabus_version.year,
                            "is_current": subject_version.syllabus_version.is_current,
                            "id": str(subject_version.syllabus_version.id)
                        }
                    
                    result["checks"]["subject_version"] = {
                        "exists": True,
                        "id": str(subject_version.id),
                        "subject": subject_version.subject.name,
                        "class_level": subject_version.class_level.name,
                        "syllabus_info": syllabus_info,
                        "is_english": subject_version.is_english,
                        "is_awali": subject_version.is_awali,
                        "periods_per_week": subject_version.subject.periods_per_week if hasattr(subject_version.subject, 'periods_per_week') else 1
                    }
                    
                    # Check if there are competences
                    competences_count = subject_version.main_competences.count()
                    result["checks"]["subject_version"]["competences_count"] = competences_count
                    
                    # Check specific learning activities count
                    try:
                        total_activities = 0
                        total_periods = 0
                        for main_comp in subject_version.main_competences.all():
                            for spec_comp in main_comp.specific_competences.all():
                                for learn_act in spec_comp.learning_activities.all():
                                    for spec_act in learn_act.specific_activities.all():
                                        total_activities += 1
                                        total_periods += spec_act.periods or 1
                        
                        result["checks"]["subject_version"]["total_activities"] = total_activities
                        result["checks"]["subject_version"]["total_periods_in_syllabus"] = total_periods
                    except Exception as e:
                        result["checks"]["subject_version"]["total_periods_in_syllabus"] = f"Could not calculate: {str(e)}"
                    
                except ValueError:
                    result["checks"]["subject_version"] = {
                        "exists": False,
                        "error": "Invalid UUID format"
                    }
                except SubjectVersion.DoesNotExist:
                    result["checks"]["subject_version"] = {
                        "exists": False,
                        "error": "Subject version not found"
                    }
            else:
                result["checks"]["subject_version"] = {
                    "exists": False,
                    "error": "Missing subject_version_id"
                }
            
            # Check annual calendar
            if calendar_id:
                try:
                    calendar_uuid = uuid.UUID(str(calendar_id))
                    annual_calendar = AnnualCalendar.objects.get(id=calendar_uuid)
                    
                    result["checks"]["annual_calendar"] = {
                        "exists": True,
                        "id": str(annual_calendar.id),
                        "institute": annual_calendar.institute,
                        "year": annual_calendar.year,
                        "status": annual_calendar.status,
                        "total_learning_days": annual_calendar.total_learning_days
                    }
                except ValueError:
                    result["checks"]["annual_calendar"] = {
                        "exists": False,
                        "error": "Invalid UUID format"
                    }
                except AnnualCalendar.DoesNotExist:
                    result["checks"]["annual_calendar"] = {
                        "exists": False,
                        "error": "Annual calendar not found"
                    }
            else:
                result["checks"]["annual_calendar"] = {
                    "exists": False,
                    "error": "Missing annual_calendar_id"
                }
            
            # Check workstation
            try:
                workstation = TeacherWorkStation.objects.filter(
                    teacher=request.user,
                    is_active=True
                ).first()
                
                result["checks"]["workstation"] = {
                    "exists": workstation is not None,
                    "school": workstation.school_name if workstation else None,
                    "id": str(workstation.id) if workstation else None
                }
            except Exception as e:
                result["checks"]["workstation"] = {
                    "exists": False,
                    "error": str(e)
                }
            
            # Check if scheme can be generated
            can_generate = all([
                result["checks"].get("subject_version", {}).get("exists", False),
                result["checks"].get("annual_calendar", {}).get("exists", False)
            ])
            
            result["can_generate_scheme"] = can_generate
            
            if can_generate:
                result["generation_note"] = "Ready to generate scheme. All syllabus versions are supported."
            else:
                result["generation_note"] = "Cannot generate scheme. Check errors above."
            
            result["success"] = True
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ Debug error: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "error": str(e),
                    "message": "Debug endpoint failed"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )