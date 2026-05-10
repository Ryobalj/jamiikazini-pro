# syllabus/views/annual_calendar_views.py

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser
from syllabus.models.annual_calendar import AnnualCalendar
from syllabus.serializers.annual_calendar_serializer import AnnualCalendarSerializer


class AnnualCalendarViewSet(viewsets.ModelViewSet):
    """
    CRUD kwa AnnualCalendar – superuser/admin pekee anaweza kufanya operesheni zote.
    
    Features:
    - Filter kwa 'year' na 'institute' kupitia query params
    - Search kwa institute (case-insensitive)
    - Default ordering by -year, institute
    """
    queryset = AnnualCalendar.objects.all().order_by('-year', 'institute')
    serializer_class = AnnualCalendarSerializer
    permission_classes = [IsAdminUser]

    # DRF Search Filter backend
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['institute']  # allows ?search=...
    ordering_fields = ['year', 'institute', 'total_learning_days']
    ordering = ['-year', 'institute']

    def get_queryset(self):
        """
        Optionally filter by year or institute from query params:
        ?year=2025&institute=Mzingi
        """
        qs = super().get_queryset()
        year = self.request.query_params.get("year")
        institute = self.request.query_params.get("institute")

        if year:
            try:
                year_int = int(year)
                qs = qs.filter(year=year_int)
            except ValueError:
                pass  # ignore invalid year filter

        if institute:
            qs = qs.filter(institute__icontains=institute)

        return qs