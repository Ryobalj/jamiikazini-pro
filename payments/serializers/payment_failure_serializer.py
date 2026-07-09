# payments/serializers/payment_failure_serializer.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from payments.models.payment_failure import PaymentFailure

class PaymentFailureSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)  # UUID irudi kama string
    formatted_amount = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    currency = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PaymentFailure
        fields = [
            "id",
            "user",
            "amount",
            "formatted_amount",
            "currency",
            "reference",
            "reason",
            "retries",
            "created",
            "updated",
        ]
        read_only_fields = ["id", "user", "formatted_amount", "created", "updated"]

    def get_formatted_amount(self, obj):
        from django.utils.formats import localize
        return localize(obj.amount)

    def get_user(self, obj):
        if not obj.user:
            return None
        return {"id": str(obj.user.id), "full_name": obj.user.full_name}

    def get_currency(self, obj):
        if not obj.currency:
            return None
        return {"code": obj.currency.code, "name": obj.currency.name}


class PaymentFailureSummarySerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)  # UUID irudi string
    formatted_amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PaymentFailure
        fields = [
            "id",
            "reference",
            "amount",
            "formatted_amount",
            "retries",
            "created_at",  # badilisha created → created_at
        ]

    def get_formatted_amount(self, obj):
        from django.utils.formats import localize
        return localize(obj.amount)