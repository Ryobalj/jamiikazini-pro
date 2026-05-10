# payments/serializers/audit_log_serializer.py

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from payments.models.audit_log import AuditLog, AuditAction
from django.utils.translation import gettext_lazy as _

class AuditLogSerializer(serializers.ModelSerializer):
    # Readable / Computed fields
    action_display = serializers.CharField(source="get_action_display", read_only=True)
    user_name = serializers.SerializerMethodField()
    content_type_name = serializers.SerializerMethodField()

    # Optional: Expandable target object data
    target_object_data = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_name",
            "action",
            "action_display",
            "content_type",
            "content_type_name",
            "object_id",
            "target_object_data",
            "description",
            "metadata",
            "ip_address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "user",
            "content_type",
            "object_id",
        ]

    def get_user_name(self, obj):
        if obj.user:
            return getattr(obj.user, "full_name", None) or str(obj.user)
        return str(_("System"))

    def get_content_type_name(self, obj):
        if obj.content_type:
            return obj.content_type.model_class().__name__
        return None

    def get_target_object_data(self, obj):
        """
        Returns serialized target object if ?expand=target_object is in request query params.
        """
        request = self.context.get("request")
        expand = request.query_params.get("expand") if request else None
        if expand == "target_object" and obj.target_object:
            from rest_framework.serializers import ModelSerializer

            # Dynamically generate a simple serializer for the target object
            class TargetSerializer(ModelSerializer):
                class Meta:
                    model = obj.target_object.__class__
                    fields = "__all__"

            return TargetSerializer(obj.target_object).data
        return None


class AuditLogCreateSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for creating logs programmatically.
    Typically used in service layers, not exposed directly to end-users.
    """

    class Meta:
        model = AuditLog
        fields = [
            "user",
            "action",
            "content_type",
            "object_id",
            "description",
            "metadata",
            "ip_address",
        ]

    def validate_action(self, value):
        if value not in AuditAction.values:
            raise serializers.ValidationError(_("Invalid action type."))
        return value

    def create(self, validated_data):
        validated_data.setdefault("metadata", {})
        return super().create(validated_data)