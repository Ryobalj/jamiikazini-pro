# construction/serializers/construction_serializer.py

from decimal import Decimal
from django.contrib.gis.geos import Point
from rest_framework import serializers

from construction.models.construction_project import ConstructionProject
from construction.models.project_bid import ProjectBid
from construction.models.project_milestone import ProjectMilestone


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = ["id", "name", "amount", "order", "status", "evidence_image", "submitted_at", "approved_at"]
        read_only_fields = fields


class ProjectBidSerializer(serializers.ModelSerializer):
    contractor_name = serializers.CharField(source="contractor.name", read_only=True)
    contractor_verified = serializers.BooleanField(source="contractor.is_verified", read_only=True)

    class Meta:
        model = ProjectBid
        fields = [
            "id", "project", "contractor", "contractor_name", "contractor_verified",
            "price", "timeline_days", "notes", "status", "created_at",
        ]
        read_only_fields = ["id", "project", "contractor_name", "contractor_verified", "status", "created_at"]


class ProjectBidCreateSerializer(serializers.Serializer):
    business_id = serializers.UUIDField()
    price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    timeline_days = serializers.IntegerField(min_value=1, max_value=3650)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ConstructionProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.full_name", read_only=True)
    contractor_name = serializers.CharField(source="contractor.name", read_only=True, default=None)
    location_lat = serializers.SerializerMethodField()
    location_lng = serializers.SerializerMethodField()
    bids = ProjectBidSerializer(many=True, read_only=True)
    milestones = ProjectMilestoneSerializer(many=True, read_only=True)

    class Meta:
        model = ConstructionProject
        fields = [
            "id", "client", "client_name", "scope_description", "location_lat", "location_lng",
            "budget_ceiling", "status", "contractor", "contractor_name", "bids", "milestones", "created_at",
        ]
        read_only_fields = fields

    def get_location_lat(self, obj):
        return obj.location.y if obj.location else None

    def get_location_lng(self, obj):
        return obj.location.x if obj.location else None


class ConstructionProjectCreateSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(write_only=True, required=False)
    lng = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = ConstructionProject
        fields = ["scope_description", "budget_ceiling", "lat", "lng"]

    def create(self, validated_data):
        lat = validated_data.pop("lat", None)
        lng = validated_data.pop("lng", None)
        if lat is not None and lng is not None:
            validated_data["location"] = Point(lng, lat, srid=4326)
        validated_data["client"] = self.context["request"].user
        return ConstructionProject.objects.create(**validated_data)


class SelectBidSerializer(serializers.Serializer):
    bid_id = serializers.UUIDField()
    # Jina la kila hatua na sehemu yake ya bei ya zabuni - jumla ya amounts
    # LAZIMA ilingane kikamilifu na bei ya zabuni iliyoshinda.
    milestones = serializers.ListField(child=serializers.DictField(), min_length=1)


class SubmitMilestoneSerializer(serializers.Serializer):
    milestone_id = serializers.UUIDField()
    evidence_image = serializers.ImageField(required=False, allow_null=True)


class ApproveMilestoneSerializer(serializers.Serializer):
    milestone_id = serializers.UUIDField()
