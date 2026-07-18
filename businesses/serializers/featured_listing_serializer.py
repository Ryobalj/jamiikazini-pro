# businesses/serializers/featured_listing_serializer.py

from datetime import timedelta
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from businesses.models.business import Business
from businesses.models.product import Product
from businesses.models.featured_listing import FeaturedListing, FeaturedPlacement
from payments.models.invoice import Invoice, InvoiceStatus

ALLOWED_DURATIONS = (7, 14, 30)


class FeaturedListingRequestSerializer(serializers.Serializer):
    """
    Mmiliki wa biashara anaomba nafasi ya matangazo (sponsored placement).
    Inaunda Invoice (kwa malipo) na FeaturedListing (is_active=False mpaka
    invoice ilipwe).
    """
    business = serializers.PrimaryKeyRelatedField(queryset=Business.objects.all())
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), required=False, allow_null=True
    )
    days = serializers.IntegerField()

    def validate_days(self, value):
        if value not in ALLOWED_DURATIONS:
            raise serializers.ValidationError(
                _("Idadi ya siku lazima iwe mojawapo ya: %(options)s") % {
                    "options": ", ".join(str(d) for d in ALLOWED_DURATIONS)
                }
            )
        return value

    def validate_business(self, value):
        request = self.context["request"]
        if value.owner_id != request.user.id:
            raise serializers.ValidationError(_("Huna ruhusa ya kutangaza biashara hii."))
        return value

    def validate(self, attrs):
        product = attrs.get("product")
        if product and product.business_id != attrs["business"].id:
            raise serializers.ValidationError(
                {"product": _("Bidhaa hii si ya biashara uliyoichagua.")}
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        business = validated_data["business"]
        product = validated_data.get("product")
        days = validated_data["days"]

        amount = FeaturedListing.calculate_amount(days)
        today = timezone.now().date()

        invoice_number = f"FT{business.id.hex[:6].upper()}{int(timezone.now().timestamp()) % 100000000}"
        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            user=request.user,
            amount=amount,
            tax=0,
            status=InvoiceStatus.PENDING,
            due_date=today + timedelta(days=3),
            created_by=request.user,
        )
        invoice.description = _("Malipo ya matangazo (sponsored placement) - siku %(days)s") % {"days": days}
        invoice.save(update_fields=["_description"])

        listing = FeaturedListing.objects.create(
            business=business,
            product=product,
            invoice=invoice,
            placement=FeaturedPlacement.HOMEPAGE,
            start_date=today,
            end_date=today + timedelta(days=days),
            amount=amount,
            is_active=False,
            created_by=request.user,
        )
        return listing


class FeaturedListingSerializer(serializers.ModelSerializer):
    invoice_status = serializers.CharField(source="invoice.status", read_only=True, default=None)
    business_name = serializers.CharField(source="business.name", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True, default=None)

    class Meta:
        model = FeaturedListing
        fields = [
            "id", "business", "business_name", "product", "product_name",
            "placement", "start_date", "end_date", "amount", "is_active",
            "invoice", "invoice_status", "created_at",
        ]
        read_only_fields = fields


class FeaturedListingPublicSerializer(serializers.ModelSerializer):
    """Kwa homepage - taarifa za umma tu za tangazo lililodhaminiwa."""
    business_id = serializers.UUIDField(source="business.id", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)
    business_description = serializers.CharField(source="business.description", read_only=True)

    product_id = serializers.UUIDField(source="product.id", read_only=True, default=None)
    product_name = serializers.CharField(source="product.name", read_only=True, default=None)
    product_image = serializers.ImageField(source="product.image", read_only=True, default=None)
    product_price = serializers.SerializerMethodField()

    class Meta:
        model = FeaturedListing
        fields = [
            "id", "business_id", "business_name", "business_description",
            "product_id", "product_name", "product_image", "product_price",
        ]

    def get_product_price(self, obj):
        return obj.product.final_price() if obj.product else None
