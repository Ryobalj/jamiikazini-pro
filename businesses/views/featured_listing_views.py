# businesses/views/featured_listing_views.py

from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from businesses.models.featured_listing import FeaturedListing
from businesses.serializers.featured_listing_serializer import (
    FeaturedListingRequestSerializer,
    FeaturedListingSerializer,
    FeaturedListingPublicSerializer,
)


class FeaturedListingRequestView(generics.CreateAPIView):
    """
    Mmiliki wa biashara anaomba nafasi ya matangazo (sponsored placement)
    kwenye homepage. Inaunda Invoice ya malipo - tangazo linakuwa hai
    (is_active) baada tu invoice kulipwa.
    """
    serializer_class = FeaturedListingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        listing = serializer.save()
        return Response(
            FeaturedListingSerializer(listing).data,
            status=status.HTTP_201_CREATED,
        )


class MyFeaturedListingsView(generics.ListAPIView):
    """Orodha ya matangazo yaliyoombwa/yanayoendelea ya biashara za mtumiaji aliyeingia."""
    serializer_class = FeaturedListingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FeaturedListing.objects.filter(
            business__owner=self.request.user
        ).select_related("business", "product", "invoice")


class ActiveFeaturedListingsView(generics.ListAPIView):
    """
    Matangazo yaliyodhaminiwa (yamelipiwa na yanaendelea) kwa ajili ya
    sehemu ya homepage - hakuna auth inayohitajika.
    """
    serializer_class = FeaturedListingPublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        today = timezone.now().date()
        return (
            FeaturedListing.objects.filter(
                is_active=True,
                start_date__lte=today,
                end_date__gte=today,
                business__is_active=True,
            )
            .select_related("business", "product")
            .order_by("-created_at")[:8]
        )
