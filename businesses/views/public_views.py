# businesses/views/public_views.py

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from businesses.models.business import Business
from businesses.models.product import Product
from businesses.serializers.business_serializer import BusinessDetailSerializer, BusinessStorefrontSerializer
from businesses.serializers.product_serializer import TrendingProductSerializer


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