# realestate/serializers/property_serializer.py

from django.contrib.gis.geos import Point
from rest_framework import serializers

from realestate.models.property_listing import PropertyListing, PropertyStatus
from realestate.models.property_image import PropertyImage


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "image", "caption", "order"]
        read_only_fields = ["id"]


class PropertyListingSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.name", read_only=True)
    owner_verified = serializers.BooleanField(source="owner.is_verified", read_only=True)
    currency_code = serializers.CharField(source="currency.code", read_only=True)
    location_lat = serializers.SerializerMethodField()
    location_lng = serializers.SerializerMethodField()
    images = PropertyImageSerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = [
            "id", "owner", "owner_name", "owner_verified", "listing_type", "property_type",
            "location_lat", "location_lng", "address_text", "price", "deposit_amount",
            "currency", "currency_code", "lease_duration_months", "bedrooms", "bathrooms",
            "size_sqm", "description", "title_deed_number", "status", "images", "cover_image",
            "created_at",
        ]
        read_only_fields = [
            "id", "owner", "owner_name", "owner_verified", "currency_code",
            "location_lat", "location_lng", "status", "images", "cover_image", "created_at",
        ]

    def get_location_lat(self, obj):
        return obj.location.y if obj.location else None

    def get_location_lng(self, obj):
        return obj.location.x if obj.location else None

    def get_cover_image(self, obj):
        first = obj.images.first()
        if not first:
            return None
        request = self.context.get("request")
        url = first.image.url
        return request.build_absolute_uri(url) if request else url


class PropertyListingCreateSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(write_only=True)
    lng = serializers.FloatField(write_only=True)

    class Meta:
        model = PropertyListing
        fields = [
            "listing_type", "property_type", "lat", "lng", "address_text", "price",
            "deposit_amount", "currency", "lease_duration_months", "bedrooms", "bathrooms",
            "size_sqm", "description", "title_deed_number",
        ]

    def validate(self, attrs):
        if attrs.get("listing_type") != "RENT" and attrs.get("deposit_amount"):
            raise serializers.ValidationError(
                {"deposit_amount": "Amana inatumika kwa RENT pekee."}
            )
        return attrs

    def create(self, validated_data):
        lat = validated_data.pop("lat")
        lng = validated_data.pop("lng")
        validated_data["location"] = Point(lng, lat, srid=4326)
        validated_data["owner"] = self.context["business"]
        return PropertyListing.objects.create(**validated_data)
