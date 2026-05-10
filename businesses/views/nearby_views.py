# businesses/views/nearby_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.utils.translation import get_language
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from businesses.models.product import Product
from businesses.models.service import Service
from businesses.models.business import Business
from businesses.serializers.product_serializer import ProductListSerializer
from businesses.serializers.service_serializer import ServiceListSerializer
from businesses.serializers.business_serializer import BusinessListSerializer


class NearbyEntitiesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = request.query_params.get("radius", 5)  # radius in km
        entity_type = request.query_params.get("type")  # product|service|business|all
        lang = get_language()

        try:
            user_location = Point(float(lng), float(lat), srid=4326)
        except (TypeError, ValueError):
            raise ValidationError({"detail": "Invalid or missing 'lat' and 'lng'"})

        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get("page_size", 10))

        # Common filters
        category = request.query_params.get("category")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        q = request.query_params.get("q", "").strip()

        data = {}

        if entity_type in ["product", "all", None]:
            products_qs = Product.objects.filter(
                is_available=True, language_code=lang
            ).annotate(
                distance=Distance("business__location", user_location)
            ).filter(
                distance__lte=float(radius) * 1000  # Filter by radius (meters)
            ).order_by("distance")

            if category:
                products_qs = products_qs.filter(category_id=category)
            if min_price:
                products_qs = products_qs.filter(price__gte=min_price)
            if max_price:
                products_qs = products_qs.filter(price__lte=max_price)
            if q:
                products_qs = products_qs.filter(
                    Q(name__icontains=q) | Q(tags__icontains=q)
                )

            page = paginator.paginate_queryset(products_qs, request)
            if page is not None:
                data["products"] = ProductListSerializer(page, many=True).data

        if entity_type in ["service", "all", None]:
            services_qs = Service.objects.filter(
                is_available=True, language_code=lang
            ).annotate(
                distance=Distance("branch__location", user_location)
            ).filter(
                distance__lte=float(radius) * 1000  # Filter by radius (meters)
            ).order_by("distance")

            if category:
                services_qs = services_qs.filter(category_id=category)
            if min_price:
                services_qs = services_qs.filter(price__gte=min_price)
            if max_price:
                services_qs = services_qs.filter(price__lte=max_price)
            if q:
                services_qs = services_qs.filter(
                    Q(name__icontains=q) | Q(tags__icontains=q)
                )

            page = paginator.paginate_queryset(services_qs, request)
            if page is not None:
                data["services"] = ServiceListSerializer(page, many=True).data

        if entity_type in ["business", "all", None]:
            # Business haina language_code field
            business_qs = Business.objects.filter(
                is_active=True
            ).annotate(
                distance=Distance("location", user_location)
            ).filter(
                distance__lte=float(radius) * 1000  # Filter by radius (meters)
            ).order_by("distance")

            if q:
                business_qs = business_qs.filter(name__icontains=q)
            if category:
                business_qs = business_qs.filter(category_id=category)

            page = paginator.paginate_queryset(business_qs, request)
            if page is not None:
                data["businesses"] = BusinessListSerializer(page, many=True).data

        return Response(data)