# syllabus/views/annual_calendar_views.py

from rest_framework import viewsets, filters
from syllabus.models.annual_calendar import AnnualCalendar
from syllabus.serializers.annual_calendar_serializer import AnnualCalendarSerializer
from syllabus.permissions import IsAdminOrReadOnly


class AnnualCalendarViewSet(viewsets.ModelViewSet):
    """
    CRUD kwa AnnualCalendar - kusoma (list/retrieve) kunaruhusiwa kwa
    mtumiaji yeyote aliyeingia (walimu wanahitaji hii kuchagua kalenda
    wakati wa kuzalisha Azimio la Kazi); kuhariri/kuunda ni kwa Admin
    pekee, kama ilivyokusudiwa awali.

    Features:
    - Filter kwa 'year' na 'institute' kupitia query params
    - Search kwa institute (case-insensitive)
    - Default ordering by -year, institute
    """
    queryset = AnnualCalendar.objects.all().order_by('-year', 'institute')
    serializer_class = AnnualCalendarSerializer
    permission_classes = [IsAdminOrReadOnly]

    # DRF Search Filter backend
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['institute']  # allows ?search=...
    ordering_fields = ['year', 'institute', 'total_learning_days']
    ordering = ['-year', 'institute']

    def get_queryset(self):
        """
        Optionally filter by year or institute from query params:
        ?year=2025&institute=Mzingi

        Also filterable by education group, so a teacher's Kidato V/VI
        scheme-builder only ever lists the 'advanced' calendar (and a
        basic-education one only ever lists 'basic') instead of every
        calendar for every class level being mixed into one dropdown:
        - ?level_group=advanced / ?level_group=basic - direct filter.
        - ?class_level=<ClassLevel name, e.g. "Kidato V"> - convenience
          filter that resolves to the matching level_group via
          AnnualCalendar.level_group_for_class_level(), so the frontend
          doesn't need to know the level_group naming itself.

        List results only ever show active (status=True) calendars -
        teachers use this list to pick which calendar to build a Scheme
        of Work against, and a calendar an admin marked inactive (e.g.
        last year's, once the new year's has been seeded) should
        disappear from that picker rather than just sit there unused.
        Retrieve/update/delete by id are untouched, so an existing
        Scheme still tied to a since-deactivated calendar keeps working.
        """
        qs = super().get_queryset()

        if self.action == "list":
            qs = qs.filter(status=True)

        year = self.request.query_params.get("year")
        institute = self.request.query_params.get("institute")
        level_group = self.request.query_params.get("level_group")
        class_level = self.request.query_params.get("class_level")

        if year:
            try:
                year_int = int(year)
                qs = qs.filter(year=year_int)
            except ValueError:
                pass  # ignore invalid year filter

        if institute:
            qs = qs.filter(institute__icontains=institute)

        if level_group:
            qs = qs.filter(level_group=level_group)
        elif class_level:
            qs = qs.filter(
                level_group=AnnualCalendar.level_group_for_class_level(class_level)
            )

        return qs