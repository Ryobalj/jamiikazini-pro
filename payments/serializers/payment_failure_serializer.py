# payments/serializers/payment_failure_serializer.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from payments.models.payment_failure import PaymentFailure

class PaymentFailureSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)  # UUID irudi kama string
    formatted_amount = serializers.SerializerMethodField(read_only=True)

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