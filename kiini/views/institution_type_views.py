# kiini/views/institution_type_views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from kiini.models.institution_type import InstitutionType
from kiini.serializers.institution_type_serializers import InstitutionTypeSerializer


class InstitutionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet ya kusoma aina za taasisi (institution types).
    - Ina ruhusu GET tu (list & retrieve).
    - Inaongezewa endpoint ya `choices/` kwa ajili ya frontend.
    """
    serializer_class = InstitutionTypeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InstitutionType.objects.all().order_by("name")

    @action(detail=False, methods=["get"], url_path="choices", url_name="choices")
    def choices(self, request):
        """
        Endpoint ya kurudisha static choices (enum) kama dropdown options.
        """
        choices = [
            {"value": choice.value, "label": choice.label}
            for choice in InstitutionType.TypeChoices
        ]
        return Response(choices)