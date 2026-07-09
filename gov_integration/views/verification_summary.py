# gov_integration/views/verification_summary.py
import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from gov_integration.models import VerificationRequest


class VerificationSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        institution = getattr(request, 'institution', None) or getattr(request.user, 'institution', None)
        if not institution:
            return Response({"detail": "Institution context missing."}, status=400)

        # Clean filters
        country = request.query_params.get('country')
        if country:
            country = country.upper().strip()

        service = request.query_params.get('service')
        if service:
            service = service.strip().upper()

        # Base queryset
        queryset = VerificationRequest.objects.filter(institution=institution)

        if country:
            queryset = queryset.filter(country=country)

        if service:
            queryset = queryset.filter(service__code__iexact=service)

        # Stats
        total = queryset.count()
        pending = queryset.filter(status='PENDING').count()
        verified = queryset.filter(status='VERIFIED').count()
        failed = queryset.filter(status='FAILED').count()

        # CSV Export
        if request.query_params.get('format') == 'csv':
            response = HttpResponse(content_type='text/csv')
            filename = f"verification_summary_{institution.name.replace(' ', '_')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            writer = csv.writer(response)
            writer.writerow(['Institution', 'Country', 'Service', 'Status', 'Count'])

            for status in ['PENDING', 'VERIFIED', 'FAILED']:
                writer.writerow([
                    institution.name,
                    country or "ALL",
                    service or "ALL",
                    status,
                    queryset.filter(status=status).count()
                ])

            return response

        # JSON Response
        return Response({
            "institution": institution.name,
            "country": country or "ALL",
            "service": service or "ALL",
            "total_requests": total,
            "pending": pending,
            "verified": verified,
            "failed": failed
        })