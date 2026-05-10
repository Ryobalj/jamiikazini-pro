# businesses/views/business_views.py

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Avg, Sum
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.text import slugify

from businesses.models.business import Business
from businesses.serializers.business_serializer import (
    BusinessSerializer,
    BusinessDetailSerializer
)
from kiini.permissions.access import IsInstitutionAdminOrReadOnly
from kiini.models.institution_type import InstitutionType
from kiini.models.institution_tier import InstitutionTier
from kiini.models.institution import Institution
from security.decorators import conditional_2fa_required


class BusinessViewSet(viewsets.ModelViewSet):
    queryset = Business.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsInstitutionAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_active", "institution"]
    search_fields = ["name", "description", "phone", "email"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BusinessDetailSerializer
        return BusinessSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Business.objects.all()
        return Business.objects.filter(owner=user)

    def create(self, request, *args, **kwargs):
        print("=== CREATE VIEW CALLED ===")
        print("Request data:", request.data)
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Save to database
        self.perform_create(serializer)
        
        # Now instance exists with ID
        instance = serializer.instance
        print(f"Instance after save: {instance}")
        print(f"Instance ID: {instance.id if instance else None}")
        
        # Get serialized data
        response_data = serializer.data
        
        # Force ID into response
        if isinstance(response_data, dict):
            if 'id' not in response_data and instance and instance.id:
                response_data = dict(response_data)
                response_data['id'] = str(instance.id)
            print(f"Final response keys: {response_data.keys()}")
            print(f"Final response ID: {response_data.get('id')}")
        
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    @conditional_2fa_required(action_type="admin_action")
    def perform_create(self, serializer):
        print("=== PERFORM CREATE CALLED ===")
        user = self.request.user
        print(f"User: {user.email}, 2FA Enabled: {user.is_2fa_enabled}")
        
        institution_id = self.request.data.get("institution")
        print(f"Institution ID from request: {institution_id}")

        if institution_id:
            institution = Institution.objects.filter(id=institution_id, owner=user).first()
            if not institution:
                print("ERROR: Institution not found or not owned by user")
                raise PermissionDenied(detail="Institution not found or not owned by you.")
            print(f"Using existing institution: {institution.id}")
        else:
            print("No institution ID, creating new one...")
            tier_name = InstitutionTier.TierChoices.SMALL
            inst_type_name = InstitutionType.TypeChoices.PRIVATE_COMPANY

            tier = InstitutionTier.objects.filter(name=tier_name).first()
            if not tier:
                tier = InstitutionTier.objects.create(
                    name=tier_name,
                    description="Small Enterprise"
                )

            inst_type = InstitutionType.objects.filter(name=inst_type_name).first()
            if not inst_type:
                inst_type = InstitutionType.objects.create(
                    name=inst_type_name,
                    description="Private Company"
                )

            name = serializer.validated_data.get("name")
            email = serializer.validated_data.get("email")
            phone = serializer.validated_data.get("phone")

            institution = Institution.objects.create(
                name=name,
                domain=slugify(name),
                email=email,
                phone=phone,
                address="",
                institution_type=inst_type,
                tier=tier,
                owner=user,
                is_active=True
            )
            print(f"Created new institution: {institution.id}")

        try:
            instance = serializer.save(owner=user, institution=institution)
            print(f"=== BUSINESS SAVED WITH ID: {instance.id} ===")
            
            # Verify in database
            exists = Business.objects.filter(id=instance.id).exists()
            print(f"Business exists in DB: {exists}")
            
        except Exception as e:
            print("=== ERROR SAVING BUSINESS ===")
            print("Error:", str(e))
            import traceback
            traceback.print_exc()
            raise

    @conditional_2fa_required(action_type="admin_action")
    def perform_update(self, serializer):
        serializer.save()

    @conditional_2fa_required(action_type="admin_action")
    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        business = self.get_object()
        range_param = request.query_params.get("range", "all")
        now = timezone.now()

        if range_param == "7d":
            start_date = now - timedelta(days=7)
        elif range_param == "30d":
            start_date = now - timedelta(days=30)
        else:
            start_date = None

        products_qs = business.products.all()
        services_qs = business.services.all()
        branches_count = business.branches.count()
        reviews_qs = business.reviews.filter(is_approved=True)

        average_rating = reviews_qs.aggregate(average=Avg("rating"))["average"]
        average_rating = round(average_rating, 1) if average_rating else None
        recent_reviews = reviews_qs.order_by("-created_at")[:5]

        orders_qs = business.orders.all()
        if start_date:
            orders_qs = orders_qs.filter(created_at__gte=start_date)

        revenue_data = {
            "last_30_days": business.orders.filter(created_at__gte=now - timedelta(days=30)).aggregate(sum=Sum("total_amount"))["sum"] or 0,
            "last_7_days": business.orders.filter(created_at__gte=now - timedelta(days=7)).aggregate(sum=Sum("total_amount"))["sum"] or 0,
            "all_time": business.orders.aggregate(sum=Sum("total_amount"))["sum"] or 0,
        }

        data = {
            "business": {
                "name": business.name,
                "is_active": business.is_active,
            },
            "stats": {
                "products_count": products_qs.count(),
                "active_products_count": products_qs.filter(is_available=True).count(),
                "inactive_products_count": products_qs.filter(is_available=False).count(),
                "services_count": services_qs.count(),
                "branches_count": branches_count,
                "reviews_count": reviews_qs.count(),
                "average_rating": average_rating,
                "recent_reviews": [
                    {
                        "user": review.user.username,
                        "rating": review.rating,
                        "comment": review.content
                    }
                    for review in recent_reviews
                ],
                "orders_count": orders_qs.count(),
                "revenue": revenue_data,
            },
        }
        return Response(data, status=status.HTTP_200_OK)