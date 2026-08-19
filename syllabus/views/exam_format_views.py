# syllabus/views/exam_format_views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from syllabus.models.exam_format import ExamFormat
from syllabus.serializers.exam_format_serializers import ExamFormatSerializer, ExamFormatListSerializer


class ExamFormatViewSet(viewsets.ModelViewSet):
    """Browse/manage exam-format templates. Teachers use ?subject=&class_level=&paper_type=
    to find formats compatible with the subject they're generating a paper
    for; a format with subject/class_level left blank is a generic
    template offered regardless of those filters."""

    permission_classes = [IsAuthenticated]
    filterset_fields = ["paper_type", "is_active"]

    def get_serializer_class(self):
        if self.action == "list":
            return ExamFormatListSerializer
        return ExamFormatSerializer

    def get_queryset(self):
        # Custom (teacher-built, "mwenyewe") formats are scratch objects
        # that exist only so a manually-built paper can reuse the normal
        # generation pipeline - they're never meant to be browsed/reused,
        # by their creator or anyone else, so exclude them here regardless
        # of who's asking.
        qs = ExamFormat.objects.select_related("subject", "class_level").prefetch_related(
            "sections__slots"
        ).filter(is_active=True, is_custom=False)
        subject = self.request.query_params.get("subject")
        class_level = self.request.query_params.get("class_level")
        if subject:
            from django.db.models import Q
            qs = qs.filter(Q(subject_id=subject) | Q(subject__isnull=True))
        if class_level:
            from django.db.models import Q
            qs = qs.filter(Q(class_level_id=class_level) | Q(class_level__isnull=True))
        return qs
