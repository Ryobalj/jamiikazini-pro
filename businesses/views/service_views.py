# businesses/views/service_views.py

from typing import Optional
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point

from businesses.models.service import Service
from businesses.serializers.service_serializer import ServiceSerializer
from kiini.permissions.access import IsInstitutionUserOrReadOnly
from security.decorators import conditional_2fa_required


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ServiceViewSet:
    - Hudumia orodha ya huduma
    - Inaruhusu filtering kwa business
    - Inatoa endpoint ya nearby services
    - Actions za admin (create/update/delete) zinahitaji 2FA
    """
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsInstitutionUserOrReadOnly]
    pagination_class = PageNumberPagination
    queryset = Service.objects.all()

    def get_queryset(self):
        """Filter services by business if 'business' query param present"""
        queryset = super().get_queryset()
        business_id = self.request.query_params.get("business")
        if business_id:
            return queryset.filter(business_id=business_id)
        return queryset

    @conditional_2fa_required(action_type="admin_action")
    def perform_create(self, serializer):
        """Create service with 2FA enforcement for admin"""
        serializer.save()

    @conditional_2fa_required(action_type="admin_action")
    def perform_update(self, serializer):
        """Update service with 2FA enforcement for admin"""
        serializer.save()

    @conditional_2fa_required(action_type="admin_action")
    def perform_destroy(self, instance):
        """Delete service with 2FA enforcement for admin"""
        instance.delete()

    @action(detail=False, methods=["get"], url_path="nearby", permission_classes=[permissions.AllowAny])
    def nearby(self, request, **kwargs) -> Response:
        """
        Rudisha huduma zilizo karibu zaidi.
        Parameta:
        - lat: latitude (decimal)
        - lng: longitude (decimal)

        Mfano:
        GET /services/nearby/?lat=-6.8&lng=39.2
        """
        lat: Optional[str] = request.query_params.get("lat")
        lng: Optional[str] = request.query_params.get("lng")

        if not lat or not lng:
            raise ValidationError({"detail": "Parameta 'lat' na 'lng' ni lazima."})
        try:
            user_location = Point(float(lng), float(lat), srid=4326)
        except (TypeError, ValueError):
            raise ValidationError({"detail": "Parameta 'lat' au 'lng' si sahihi."})

        qs = (
            self.get_queryset()
            .annotate(distance=Distance("business__location", user_location))
            .order_by("distance")
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)