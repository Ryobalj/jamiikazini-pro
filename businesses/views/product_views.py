# businesses/views/product_views.py

import logging
from decimal import Decimal, InvalidOperation

from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.conf import settings
from django.utils.translation import get_language
from django.db import models
from django.utils.text import slugify

from businesses.models.product import Product
from businesses.models.business import Business
from businesses.serializers.product_serializer import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductSerializer,
)
from kiini.helpers.domain import generate_subdomain_url

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet ya kusoma na kuunda products (list, create, retrieve, update, delete).
    Inajumuisha filters kwa business, branch, featured, price range,
    na inazingatia language ya mtumiaji.
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        lang = get_language()
        qs = Product.objects.filter(language_code=lang)

        # Filter by business/branch
        business_pk = self.kwargs.get("business_pk")
        branch_pk = self.kwargs.get("branch_pk")

        if branch_pk:
            qs = qs.filter(business__branches__pk=branch_pk)
        elif business_pk:
            qs = qs.filter(business__pk=business_pk)

        # Filter: is_available
        is_available = self.request.query_params.get("is_available")
        if is_available is not None:
            val = is_available.lower()
            if val in ["true", "1"]:
                qs = qs.filter(is_available=True)
            elif val in ["false", "0"]:
                qs = qs.filter(is_available=False)

        # Filter: by ProductCategory slug
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)

        # Filter: legacy free-text tag search
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__contains=[tag])

        # Filter: is_featured
        is_featured = self.request.query_params.get("is_featured")
        if is_featured is not None:
            val = is_featured.lower()
            if val in ["true", "1"]:
                qs = qs.filter(is_featured=True)
            elif val in ["false", "0"]:
                qs = qs.filter(is_featured=False)

        # Filter: Price Range
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price and max_price:
            try:
                if float(min_price) > float(max_price):
                    raise ValidationError({"price_range": "min_price cannot be greater than max_price"})
            except ValueError:
                raise ValidationError({"price_range": "Price filters must be numeric"})
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        return qs.select_related("business", "business__institution", "category")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        if self.action == "list":
            return ProductListSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        business_id = self.kwargs.get("business_pk")
        try:
            business = Business.objects.get(pk=business_id)
        except Business.DoesNotExist:
            raise ValidationError({"business": "Business not found"})
        
        if business.owner != self.request.user:
            raise PermissionDenied("You don't have permission to add products to this business")
        
        name = serializer.validated_data.get("name")
        slug = slugify(name)
        
        counter = 1
        original_slug = slug
        while Product.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        tags = serializer.validated_data.get("tags", [])
        if isinstance(tags, str):
            try:
                import json
                tags = json.loads(tags)
            except:
                tags = [t.strip() for t in tags.split(",") if t.strip()]
        
        product = serializer.save(business=business, slug=slug, tags=tags)
        
        # Index to Elasticsearch if enabled
        if not settings.DEBUG and getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.documents.product_document import ProductDocument
            try:
                doc = ProductDocument(meta={'id': product.id})
                doc.update(product)
            except Exception as e:
                logger.warning(f"Failed to index product to Elasticsearch: {e}")

    def perform_update(self, serializer):
        product = self.get_object()
        if product.business.owner != self.request.user:
            raise PermissionDenied("You don't have permission to update this product")
        
        if "name" in serializer.validated_data:
            name = serializer.validated_data["name"]
            slug = slugify(name)
            counter = 1
            original_slug = slug
            while Product.objects.filter(slug=slug).exclude(pk=product.pk).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            serializer.validated_data["slug"] = slug
        
        tags = serializer.validated_data.get("tags", product.tags)
        if isinstance(tags, str):
            try:
                import json
                tags = json.loads(tags)
            except:
                tags = [t.strip() for t in tags.split(",") if t.strip()]
        serializer.validated_data["tags"] = tags
        
        product = serializer.save()
        
        # Update Elasticsearch if enabled
        if not settings.DEBUG and getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.documents.product_document import ProductDocument
            try:
                doc = ProductDocument(meta={'id': product.id})
                doc.update(product)
            except Exception as e:
                logger.warning(f"Failed to update product in Elasticsearch: {e}")

    def perform_destroy(self, instance):
        if instance.business.owner != self.request.user:
            raise PermissionDenied("You don't have permission to delete this product")
        
        # Delete from Elasticsearch if enabled
        if not settings.DEBUG and getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.documents.product_document import ProductDocument
            try:
                doc = ProductDocument.get(id=instance.id)
                doc.delete()
            except Exception as e:
                logger.warning(f"Failed to delete product from Elasticsearch: {e}")
        
        instance.delete()

    @action(detail=True, methods=["post"])
    def restock(self, request, slug=None, **kwargs):
        """
        Ongeza stock ya bidhaa (mmiliki wa biashara pekee). Hii ndiyo njia rasmi
        ya kuongeza quantity_in_stock - si kuhariri field moja kwa moja kupitia
        update ya jumla - ili kuwa na audit trail wazi ya kila ongezeko.
        """
        product = self.get_object()
        if product.business.owner != request.user:
            raise PermissionDenied("You don't have permission to restock this product")

        try:
            quantity = Decimal(str(request.data.get("quantity")))
        except (TypeError, ValueError, InvalidOperation):
            raise ValidationError({"quantity": "Weka namba sahihi ya kuongeza."})
        if quantity <= 0:
            raise ValidationError({"quantity": "Kiasi cha kuongeza lazima kiwe zaidi ya sifuri."})

        product.quantity_in_stock = models.F("quantity_in_stock") + quantity
        product.save(update_fields=["quantity_in_stock"])
        product.refresh_from_db(fields=["quantity_in_stock"])

        logger.info(
            "Product restocked: product=%s business=%s by=%s +%s -> %s",
            product.id, product.business_id, request.user.id, quantity, product.quantity_in_stock,
        )

        return Response({
            "id": str(product.id),
            "quantity_in_stock": product.quantity_in_stock,
        })

    @action(detail=False, methods=["get"])
    def nearby(self, request, **kwargs):
        """
        List products sorted by proximity to user's location + supports filters.
        """
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")

        if not lat or not lng:
            raise ValidationError({"detail": "Both 'lat' and 'lng' query parameters are required."})

        try:
            user_location = Point(float(lng), float(lat), srid=4326)
        except (TypeError, ValueError):
            raise ValidationError({"detail": "Invalid coordinates."})

        qs = self.get_queryset().annotate(
            distance=Distance("business__location", user_location)
        ).order_by("distance")

        results = self.paginate_queryset(qs)
        serializer = ProductListSerializer(results, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def featured(self, request, **kwargs):
        """
        List featured products (with optional filters).
        """
        qs = self.get_queryset().filter(is_featured=True)
        results = self.paginate_queryset(qs)
        if results is not None:
            serializer = ProductListSerializer(results, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ProductListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def search(self, request, **kwargs):
        """
        Search for products by name or tags.
        Supports filters and pagination.
        """
        query = request.query_params.get("q", "").strip()
        if not query:
            raise ValidationError({"q": "Search term is required."})

        qs = self.get_queryset().filter(
            models.Q(name__icontains=query) | models.Q(tags__icontains=query)
        )

        results = self.paginate_queryset(qs)
        if results is not None:
            serializer = ProductListSerializer(results, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ProductListSerializer(qs, many=True)
        return Response(serializer.data)


class ProductListByProximityView(generics.ListAPIView):
    """
    List products sorted by proximity to user if location provided,
    otherwise fallback to recent products.
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        lang = get_language()
        qs = Product.objects.filter(is_available=True, language_code=lang).select_related(
            "business", "business__institution", "category"
        )

        try:
            lat = float(self.request.query_params.get("lat"))
            lng = float(self.request.query_params.get("lng"))
            user_location = Point(lng, lat, srid=4326)
            qs = qs.annotate(distance=Distance("business__location", user_location)).order_by("distance")
        except (TypeError, ValueError):
            qs = qs.order_by("-created_at")

        return qs


@api_view(["GET"])
def generate_product_url(request, slug):
    """
    Generate full URL for a given product via subdomain.
    """
    try:
        product = Product.objects.select_related("business", "business__institution").get(slug=slug)
        institution = getattr(product.business, "institution", None)
        base_domain = getattr(institution, "domain", None) or "jamiikazini.com"
        domain = generate_subdomain_url(base_domain, path=f"/products/{product.slug}/")
        return Response({"url": domain})
    except Product.DoesNotExist:
        return Response({"detail": "Product not found."}, status=404)