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
            "slug", "created_at", "updated_at"
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
        else:
            institution = validated_data.get("institution")
    
        name = validated_data.get("name", "").strip().lower().replace(" ", "-")
        institution_name = institution.name.strip().lower().replace(" ", "-")
        domain = institution.domain.strip().lower()
    
        if name != institution_name:
            validated_data["website"] = f"{name}.{domain}"
        else:
            validated_data["website"] = domain
        
        business = super().create(validated_data)
        print(f"Business created with ID: {business.id}")
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
        
        print("FORCED data keys:", data.keys())
        print("FORCED id:", data.get('id'))
        
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


class BusinessMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ["id", "name", "slug"]