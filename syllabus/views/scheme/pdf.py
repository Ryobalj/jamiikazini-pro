# syllabus/views/scheme/pdf.py

from rest_framework.permissions import IsAuthenticated
from syllabus.permissions import CanDownloadPDF
from syllabus.views.scheme.create import SchemeCreateAPIView


class SchemePDFAPIView(SchemeCreateAPIView):
    """
    Force PDF generation
    """
    permission_classes = [IsAuthenticated, CanDownloadPDF]

    def create(self, request, *args, **kwargs):
        request.query_params._mutable = True
        request.query_params["format"] = "pdf"
        return super().create(request, *args, **kwargs)