# businesses/views/public_views.py

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from businesses.models.product import Product
from businesses.models.service import Service
from businesses.serializers.business_serializer import (
    BusinessDetailSerializer, BusinessStorefrontSerializer, VerifiedBusinessCardSerializer,
)
from businesses.serializers.category_serializer import BusinessCategorySerializer
from businesses.serializers.product_serializer import TrendingProductSerializer
from businesses.serializers.service_serializer import TrendingServiceSerializer


class PublicBusinessDetailView(generics.RetrieveAPIView):
    queryset = Business.objects.filter(is_active=True)
    serializer_class = BusinessDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class BusinessStorefrontView(generics.RetrieveAPIView):
    """
    Ukurasa wa umma wa duka la biashara - kwa wateja: taarifa za biashara,
    katalogi ya bidhaa/huduma zinazopatikana, na muhtasari wa maoni.
    """
    queryset = Business.objects.filter(is_active=True).select_related(
        "category", "category__parent", "owner"
    )
    serializer_class = BusinessStorefrontSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class BusinessResolveDomainView(generics.RetrieveAPIView):
    """
    GET /businesses/resolve-domain/?domain=<label>
    Sawa na BusinessStorefrontView lakini kutafutwa kwa subdomain badala ya
    pk - hii ndiyo endpoint inayotumiwa na frontend wakati mtumiaji anafika
    kupitia <domain>.jamiikazini.com badala ya jamiikazini.com/store/<uuid>.
    """
    queryset = Business.objects.filter(is_active=True).select_related(
        "category", "category__parent", "owner"
    )
    serializer_class = BusinessStorefrontSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        domain = (self.request.query_params.get("domain") or "").strip().lower()
        if not domain:
            raise NotFound("Weka ?domain=.")
        return get_object_or_404(self.get_queryset(), domain=domain)


class TrendingProductsView(generics.ListAPIView):
    """
    Bidhaa zinazouzwa/kuagizwa zaidi hivi karibuni (siku 30 zilizopita),
    kwa ajili ya sehemu ya "Bidhaa Zinazotrend" kwenye homepage ya jamiikazini.
    Bidhaa zisizo na order bado zinaweza kuonekana (kujaza nafasi) kwa
    kutumia is_featured/created_at kama fallback ya kupanga.
    """
    serializer_class = TrendingProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        since = timezone.now() - timedelta(days=30)
        return (
            Product.objects.filter(is_available=True, business__is_active=True)
            .select_related("business", "currency")
            .annotate(
                order_count=Count(
                    "order_items",
                    filter=Q(order_items__created_at__gte=since),
                )
            )
            .order_by("-order_count", "-is_featured", "-created_at")[:12]
        )


class TrendingServicesView(generics.ListAPIView):
    """
    Huduma zinazoagizwa/kubuk zaidi hivi karibuni (siku 30 zilizopita), sawa
    na TrendingProductsView lakini kwa Service - kwa ajili ya sehemu ya
    "Huduma Zinazotrend" kwenye homepage.
    """
    serializer_class = TrendingServiceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        since = timezone.now() - timedelta(days=30)
        return (
            Service.objects.filter(is_available=True, business__is_active=True)
            .select_related("business")
            .annotate(
                order_count=Count(
                    "order_items",
                    filter=Q(order_items__created_at__gte=since),
                )
            )
            .order_by("-order_count", "-created_at")[:8]
        )


class VerifiedBusinessesView(generics.ListAPIView):
    """
    Biashara chache zilizothibitishwa (is_verified) hivi karibuni - kwa ajili
    ya sehemu ya "Biashara Zilizothibitishwa" kwenye homepage.
    """
    serializer_class = VerifiedBusinessCardSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            Business.objects.filter(is_verified=True, is_active=True)
            .select_related("category")
            .order_by("-created_at")[:6]
        )


class TopCategoriesView(generics.ListAPIView):
    """
    Aina kuu (top-level) za biashara - kwa ajili ya sehemu ya "Vinjari kwa
    Aina" kwenye homepage.
    """
    serializer_class = BusinessCategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            BusinessCategory.objects.filter(parent__isnull=True, is_active=True)
            .order_by("name")[:8]
        )


class BusinessesByCategoryView(generics.ListAPIView):
    """
    Biashara hai ndani ya aina fulani (au aina zake ndogo) - inatumika na
    ukurasa wa 'Vinjari kwa Aina' wakati mtumiaji anabofya aina moja
    kwenye homepage.
    """
    serializer_class = VerifiedBusinessCardSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        slug = self.kwargs["slug"]
        return (
            Business.objects.filter(is_active=True)
            .filter(Q(category__slug=slug) | Q(category__parent__slug=slug))
            .select_related("category")
            .order_by("-is_verified", "-created_at")
        )