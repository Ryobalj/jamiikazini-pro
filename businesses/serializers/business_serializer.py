# businesses/serializers/business_serializer.py

from rest_framework import serializers
from django.contrib.gis.geos import Point

from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from accounts.models import User
from kiini.models.institution import Institution
from accounts.serializers import UserMinimalSerializer


class BusinessSerializer(serializers.ModelSerializer):
    institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(),
        required=False,
        allow_null=True,
    )

    owner = UserMinimalSerializer(read_only=True)

    category = serializers.PrimaryKeyRelatedField(
        queryset=BusinessCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    lat = serializers.FloatField(write_only=True, required=False)
    lon = serializers.FloatField(write_only=True, required=False)

    location_lat = serializers.SerializerMethodField()
    location_lon = serializers.SerializerMethodField()

    institution_name = serializers.CharField(source="institution.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Business
        fields = [
            "id",
            "institution", "institution_name",
            "owner",
            "name", "description",
            "category", "category_name",
            "lat", "lon", "location_lat", "location_lon",
            "phone", "email", "website",
            "is_active", "is_verified",
            "broker_commission_rate", "deals_in_imports", "deals_in_agriculture",
            "slug", "domain", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "slug", "created_at", "updated_at",
            "location_lat", "location_lon",
            "is_verified", "owner",
            "institution_name", "category_name"
        ]

    def get_location_lat(self, obj):
        if obj is None:
            return None
        if isinstance(obj, dict):
            loc = obj.get('location')
            return loc.y if loc else None
        return obj.location.y if obj.location else None

    def get_location_lon(self, obj):
        if obj is None:
            return None
        if isinstance(obj, dict):
            loc = obj.get('location')
            return loc.x if loc else None
        return obj.location.x if obj.location else None

    def validate_name(self, value):
        return value

    def create(self, validated_data):
        lat = validated_data.pop("lat", None)
        lon = validated_data.pop("lon", None)
    
        if lat is not None and lon is not None:
            validated_data["location"] = Point(lon, lat)
    
        user = self.context["request"].user
        validated_data["owner"] = user
    
        institution = validated_data.get("institution")
        if not institution:
            default_name = validated_data.get("name", "Institution").strip()
            institution = Institution.objects.create(
                name=default_name,
                domain=f"{default_name.lower().replace(' ', '-')}.local"
            )
            validated_data["institution"] = institution
        elif not institution.domain:
            # Domain ni hiari wakati wa kuunda taasisi - kama haijawekwa, tengeneza
            # default salama badala ya ku-crash kwenye .strip() ya None hapa chini.
            institution.domain = f"{institution.name.strip().lower().replace(' ', '-')}.local"
            institution.save(update_fields=["domain"])

        name = validated_data.get("name", "").strip().lower().replace(" ", "-")
        institution_name = institution.name.strip().lower().replace(" ", "-")
        domain = institution.domain.strip().lower()

        if name != institution_name:
            validated_data["website"] = f"{name}.{domain}"
        else:
            validated_data["website"] = domain

        business = super().create(validated_data)
        return business

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # FORCE ID - override whatever DRF did
        if hasattr(instance, 'id'):
            data['id'] = str(instance.id)
        elif hasattr(instance, 'pk'):
            data['id'] = str(instance.pk)
        elif isinstance(instance, dict) and 'id' in instance:
            data['id'] = instance['id']

        return data

    def update(self, instance, validated_data):
        lat = validated_data.pop("lat", None)
        lon = validated_data.pop("lon", None)

        if lat is not None and lon is not None:
            validated_data["location"] = Point(lon, lat)

        return super().update(instance, validated_data)


class BusinessListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)
    distance = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            "id", "name", "slug", "description",
            "category_name", "institution_name",
            "phone", "email", "website",
            "is_active", "is_verified",
            "distance", "location"
        ]

    def get_distance(self, obj):
        if hasattr(obj, "distance") and obj.distance is not None:
            return round(obj.distance.km, 2)
        return None

    def get_location(self, obj):
        if hasattr(obj, 'location') and obj.location:
            return {
                "latitude": obj.location.y,
                "longitude": obj.location.x
            }
        return None


class BusinessDetailSerializer(serializers.ModelSerializer):
    institution = serializers.StringRelatedField()
    owner = UserMinimalSerializer(read_only=True)
    category = serializers.StringRelatedField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            "id",
            "name",
            "description",
            "category",
            "institution",
            "owner",
            "location",
            "phone",
            "email",
            "website",
            "is_active",
            "is_verified",
            "slug",
            "created_at",
            "updated_at",
        ]

    def get_location(self, obj):
        if hasattr(obj, 'location') and obj.location:
            return {
                "latitude": obj.location.y,
                "longitude": obj.location.x
            }
        return None


# Kategoria za mzazi zinazoashiria biashara hii "storefront_type" gani ionekane -
# ni kidokezo cha muonekano (theming) tu, si kuficha sehemu - bidhaa/huduma zilizopo
# zinaonekana daima bila kujali aina.
INFORMAL_CATEGORY_SLUGS = {
    "informal-individual-services", "driver", "food-vendor",
    "small-scale-farmer", "artisan-repair", "small-shopkeeper",
}
SERVICE_FOCUSED_CATEGORY_SLUGS = {
    "professional-services", "healthcare", "education", "financial-services",
    "legal", "accounting", "consulting", "marketing", "clinics", "pharmacies",
    "diagnostic-centers", "schools", "training-centers", "e-learning",
    "banking", "insurance", "microfinance", "investments",
}


def _storefront_type_for(category):
    if not category:
        return "products"
    slugs = {category.slug}
    if category.parent:
        slugs.add(category.parent.slug)
    if slugs & INFORMAL_CATEGORY_SLUGS:
        return "informal"
    if slugs & SERVICE_FOCUSED_CATEGORY_SLUGS:
        return "services"
    return "products"


class BusinessStorefrontSerializer(serializers.ModelSerializer):
    """
    Ukurasa wa umma wa biashara - kwa wateja, si mmiliki. Inajumuisha katalogi ya
    bidhaa/huduma ili mteja aone na aweze kununua, si takwimu za ndani za mmiliki.
    """
    owner = UserMinimalSerializer(read_only=True)
    category = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    storefront_type = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    institution = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()
    review_summary = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            "id", "name", "description", "slug",
            "category", "category_name", "storefront_type",
            "owner", "location", "institution", "phone", "email", "website",
            "is_active", "is_verified",
            "products", "services", "review_summary",
            "created_at", "updated_at",
        ]

    def get_category(self, obj):
        if not obj.category:
            return None
        return {
            "id": str(obj.category.id),
            "name": obj.category.name,
            "slug": obj.category.slug,
            "parent_name": obj.category.parent.name if obj.category.parent else None,
            "parent_slug": obj.category.parent.slug if obj.category.parent else None,
        }

    def get_storefront_type(self, obj):
        return _storefront_type_for(obj.category)

    def get_location(self, obj):
        if obj.location:
            return {"latitude": obj.location.y, "longitude": obj.location.x}
        return None

    def get_institution(self, obj):
        # Kila Business ina Institution (huundwa moja kwa moja kama haikutolewa
        # wakati wa usajili - angalia BusinessSerializer.create()), lakini nyingi
        # ni "wrapper" ya duka moja tu. Tunaonyesha kiungo cha "sehemu ya jengo"
        # tu pale taasisi ina zaidi ya duka moja hai (jengo la kweli lenye
        # wapangaji wengi, mf. mall), la sivyo ni kelele isiyo na maana kwa duka
        # moja moja.
        institution = obj.institution
        if not institution or not institution.is_active:
            return None
        tenant_count = institution.businesses.filter(is_active=True).count()
        if tenant_count <= 1:
            return None
        return {"id": str(institution.id), "name": institution.name, "tenant_count": tenant_count}

    def get_products(self, obj):
        from businesses.serializers.product_serializer import ProductListSerializer
        qs = obj.products.filter(is_available=True).order_by("-is_featured", "-created_at")
        return ProductListSerializer(qs, many=True).data

    def get_services(self, obj):
        from businesses.serializers.service_serializer import ServiceListSerializer
        qs = obj.services.all().order_by("-created_at")
        return ServiceListSerializer(qs, many=True).data

    def get_review_summary(self, obj):
        from django.db.models import Avg, Count
        agg = obj.reviews.aggregate(average=Avg("rating"), count=Count("id"))
        return {
            "average": round(agg["average"], 1) if agg["average"] else None,
            "count": agg["count"] or 0,
        }


class BusinessMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ["id", "name", "slug"]