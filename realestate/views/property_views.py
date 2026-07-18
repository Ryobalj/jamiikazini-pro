# realestate/views/property_views.py

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from businesses.models.business import Business
from realestate.models.property_listing import PropertyListing, PropertyStatus
from realestate.models.property_image import PropertyImage
from realestate.serializers.property_serializer import (
    PropertyListingSerializer,
    PropertyListingCreateSerializer,
    PropertyImageSerializer,
)


class PropertyListingViewSet(viewsets.ModelViewSet):
    """
    Matangazo ya mali isiyohamishika. List/retrieve ni ya umma (AllowAny).
    List INAONYESHA status=AVAILABLE pekee - hii ndiyo utekelezaji wa lazima
    wa "tangazo lisionekane tena baada ya kuchukuliwa" (RESERVED/RENTED/SOLD
    hazionekani kwenye orodha ya utafutaji, hata kama zinapatikana kwa
    retrieve ya moja kwa moja kwa mwenye kiungo/ombi lililopo).
    """
    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = PropertyListingSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return PropertyListingCreateSerializer
        return PropertyListingSerializer

    def get_queryset(self):
        qs = PropertyListing.objects.select_related("owner", "currency").prefetch_related("images")

        if self.action == "list":
            qs = qs.filter(status=PropertyStatus.AVAILABLE)

            listing_type = self.request.query_params.get("listing_type")
            property_type = self.request.query_params.get("property_type")
            min_price = self.request.query_params.get("min_price")
            max_price = self.request.query_params.get("max_price")
            lat = self.request.query_params.get("lat")
            lng = self.request.query_params.get("lng")
            radius = self.request.query_params.get("radius", 20)

            if listing_type:
                qs = qs.filter(listing_type=listing_type)
            if property_type:
                qs = qs.filter(property_type=property_type)
            if min_price:
                qs = qs.filter(price__gte=min_price)
            if max_price:
                qs = qs.filter(price__lte=max_price)
            if lat and lng:
                try:
                    user_location = Point(float(lng), float(lat), srid=4326)
                except (TypeError, ValueError):
                    raise ValidationError({"detail": "lat/lng batili."})
                qs = qs.annotate(distance=Distance("location", user_location)).filter(
                    distance__lte=float(radius) * 1000
                ).order_by("distance")

        return qs

    def _get_owned_business(self, business_id, user):
        try:
            business = Business.objects.get(pk=business_id)
        except (Business.DoesNotExist, ValueError):
            raise NotFound("Biashara haipatikani.")
        if business.owner_id != user.id:
            raise PermissionDenied("Huna ruhusa ya biashara hii.")
        return business

    def create(self, request, *args, **kwargs):
        business_id = request.data.get("business")
        if not business_id:
            raise ValidationError({"business": "Chagua biashara inayotangaza mali hii."})
        business = self._get_owned_business(business_id, request.user)

        serializer = self.get_serializer(data=request.data, context={"business": business, "request": request})
        serializer.is_valid(raise_exception=True)
        listing = serializer.save()
        return Response(PropertyListingSerializer(listing, context={"request": request}).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        listing = self.get_object()
        if listing.owner.owner_id != request.user.id:
            raise PermissionDenied("Huna ruhusa ya tangazo hili.")
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """Matangazo ya biashara za mtumiaji huyu - bila kuchuja status."""
        qs = PropertyListing.objects.filter(
            owner__owner=request.user
        ).select_related("owner", "currency").prefetch_related("images").order_by("-created_at")
        return Response(PropertyListingSerializer(qs, many=True, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="images")
    def upload_image(self, request, pk=None):
        listing = self.get_object()
        if listing.owner.owner_id != request.user.id:
            raise PermissionDenied("Huna ruhusa ya tangazo hili.")

        serializer = PropertyImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = request.data.get("order") or listing.images.count()
        image = PropertyImage.objects.create(
            property=listing, image=serializer.validated_data["image"],
            caption=serializer.validated_data.get("caption", ""), order=order,
        )
        return Response(PropertyImageSerializer(image).data, status=status.HTTP_201_CREATED)
