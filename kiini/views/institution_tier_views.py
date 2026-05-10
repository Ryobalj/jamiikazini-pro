# kiini/views/institution_tier_views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from kiini.models.institution_tier import InstitutionTier
from kiini.serializers.institution_tier_serializers import InstitutionTierSerializer


class InstitutionTierViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet ya kusoma tiers za taasisi (Institution Tiers).
    - Ina ruhusu GET (list & retrieve).
    - Inaongezewa endpoint ya `choices/` kwa frontend.
    """
    queryset = InstitutionTier.objects.all().order_by("name")
    serializer_class = InstitutionTierSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="choices", url_name="choices")
    def choices(self, request):
        """
        Endpoint ya kurudisha static choices za enum kwa ajili ya dropdown.
        """
        choices = [
            {"value": choice.value, "label": choice.label}
            for choice in InstitutionTier.TierChoices
        ]
        return Response(choices)