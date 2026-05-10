# payments/serializers/bulk_payment_serializer.py

from django.db import transaction
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from payments.models.bulk_payment import (
    BulkPaymentTemplate,
    BulkPaymentExecution
)


# -------------------------
# TEMPLATE SERIALIZERS
# -------------------------

class BulkPaymentTemplateSummarySerializer(serializers.ModelSerializer):
    """Muhtasari wa haraka wa template za malipo mengi"""
    total_payments = serializers.IntegerField(read_only=True)
    total_amount = serializers.FloatField(read_only=True)

    class Meta:
        model = BulkPaymentTemplate
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "total_payments",
            "total_amount",
            "created_at",
        ]


class BulkPaymentTemplateSerializer(serializers.ModelSerializer):
    """Serializer kamili ya CRUD ya BulkPaymentTemplate"""
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    total_payments = serializers.IntegerField(read_only=True)
    total_amount = serializers.FloatField(read_only=True)

    class Meta:
        model = BulkPaymentTemplate
        fields = [
            "id",
            "name",
            "description",
            "payments_data",
            "metadata",
            "is_active",
            "total_payments",
            "total_amount",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_by_name", "created_at", "updated_at"]

    def validate_payments_data(self, value):
        """Validates the payments_data consistency before save"""
        if not isinstance(value, list):
            raise serializers.ValidationError(_("Data ya malipo lazima iwe orodha"))
        if len(value) == 0:
            raise serializers.ValidationError(_("Orodha ya malipo haiwezi kuwa tupu"))
        if len(value) > 1000:
            raise serializers.ValidationError(_("Haiwezi kuzidi malipo 1000 kwa template moja"))

        for i, payment in enumerate(value):
            if not isinstance(payment, dict):
                raise serializers.ValidationError(_(f"Malipo katika nafasi {i} lazima iwe dict"))
            if "recipient_user_id" not in payment or "amount" not in payment:
                raise serializers.ValidationError(
                    _(f"Malipo katika nafasi {i} yanakosa 'recipient_user_id' au 'amount'")
                )
            try:
                amount = float(payment["amount"])
                if amount <= 0:
                    raise serializers.ValidationError(
                        _(f"Kiasi cha malipo katika nafasi {i} si sahihi: {amount}")
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    _(f"Kiasi cha malipo katika nafasi {i} si muundo sahihi")
                )
        return value

    def create(self, validated_data):
        """Assign user automatically"""
        user = self.context["request"].user
        validated_data["created_by"] = user
        return super().create(validated_data)


# -------------------------
# EXECUTION SERIALIZERS - PRODUCTION READY
# -------------------------

class BulkPaymentExecutionSummarySerializer(serializers.ModelSerializer):
    """Muhtasari wa utekelezaji wa malipo mengi"""
    success_rate = serializers.FloatField(read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)
    executed_by_name = serializers.CharField(source="executed_by.get_full_name", read_only=True)

    class Meta:
        model = BulkPaymentExecution
        fields = [
            "id",
            "template_name",
            "status",
            "total_payments",
            "successful_count",
            "failed_count",
            "success_rate",
            "executed_by_name",
            "executed_at",
            "completed_at",
        ]


class BulkPaymentExecutionSerializer(serializers.ModelSerializer):
    """Taarifa kamili za utekelezaji"""
    executed_by_name = serializers.CharField(source="executed_by.get_full_name", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)
    success_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = BulkPaymentExecution
        fields = [
            "id",
            "template",
            "template_name",
            "executed_by",
            "executed_by_name",
            "total_payments",
            "successful_count",
            "failed_count",
            "results",
            "idempotency_key",
            "status",
            "executed_at",
            "completed_at",
            "metadata",
            "success_rate",
        ]
        read_only_fields = [
            "executed_by",
            "executed_by_name",
            "executed_at",
            "completed_at",
            "status",
            "results",
            "successful_count",
            "failed_count",
            "total_payments",
            "success_rate",
        ]


class BulkPaymentExecutionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer ya kuanzisha utekelezaji mpya wa malipo mengi (production-safe).

    - Inalinda dhidi ya marudio kwa idempotency_key.
    - Inahakikisha template iko hai na ina data.
    - Inaweka total_payments kabla ya ku-create.
    - Inafanya create ndani ya transaction.atomic().
    """

    template_name = serializers.CharField(source="template.name", read_only=True)

    class Meta:
        model = BulkPaymentExecution
        fields = [
            "id",
            "template",
            "template_name",
            "idempotency_key",
            "metadata",
        ]
        extra_kwargs = {
            "idempotency_key": {"required": True}
        }

    def validate(self, attrs):
        template = attrs.get("template")
        idempotency_key = attrs.get("idempotency_key")

        # 1. Template must exist and be active
        if not template or not getattr(template, "is_active", False):
            raise serializers.ValidationError({"template": _("Template haipo au imezimwa.")})

        # 2. Template must have payments_data
        if not getattr(template, "payments_data", None) or len(template.payments_data) == 0:
            raise serializers.ValidationError({"template": _("Template haina data ya malipo.")})

        # 3. Idempotency: ensure this key hasn't been used already
        if BulkPaymentExecution.objects.filter(idempotency_key=idempotency_key).exists():
            raise serializers.ValidationError({
                "idempotency_key": _("Utekelezaji wenye ufunguo huu tayari upo — zuia marudio.")
            })

        # 4. Derive and set total_payments from template (single source of truth)
        attrs["total_payments"] = template.total_payments

        return attrs

    def create(self, validated_data):
        """
        Create execution record in an atomic transaction.
        Important: we only create the execution record here and return it.
        Actual processing must be handled by a background worker (Celery/RQ) which will
        load template.payments_data or execution.metadata and process the transfers.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        with transaction.atomic():
            execution = BulkPaymentExecution.objects.create(
                executed_by=user,
                template=validated_data.get("template"),
                total_payments=validated_data.get("total_payments"),
                idempotency_key=validated_data.get("idempotency_key"),
                metadata=validated_data.get("metadata", {}),
                status=BulkPaymentExecution.Status.PROCESSING,
            )

        return execution