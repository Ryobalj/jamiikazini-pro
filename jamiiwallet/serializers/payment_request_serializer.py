# jamiiwallet/serializers/payment_request_serializer.py

from decimal import Decimal

from rest_framework import serializers

from jamiiwallet.models.payment_request import PaymentRequest
from jamiiwallet.serializers.transfer_serializer import find_recipient


class PaymentRequestSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payer_identifier = serializers.CharField(write_only=True)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)
    reference = serializers.CharField(read_only=True)
    requester_name = serializers.CharField(source='requester.full_name', read_only=True)
    payer_name = serializers.CharField(source='payer.full_name', read_only=True)
    direction = serializers.SerializerMethodField()

    class Meta:
        model = PaymentRequest
        fields = [
            'id', 'amount', 'payer_identifier', 'requester_name', 'payer_name',
            'note', 'reference', 'status', 'direction', 'created_at', 'responded_at',
        ]
        read_only_fields = [
            'id', 'reference', 'status', 'requester_name', 'payer_name',
            'direction', 'created_at', 'responded_at',
        ]

    def get_direction(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and obj.requester_id == user.id:
            return "outgoing"
        return "incoming"

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, data):
        request = self.context.get("request")
        requester = getattr(request, "user", None)

        payer = find_recipient(data.get("payer_identifier"))
        if not payer:
            raise serializers.ValidationError({"payer_identifier": "Mlipaji hakupatikana."})
        if payer.id == requester.id:
            raise serializers.ValidationError({"payer_identifier": "Huwezi kujiomba pesa mwenyewe."})

        data["payer"] = payer
        return data

    def create(self, validated_data):
        validated_data.pop("payer_identifier", None)
        payer = validated_data.pop("payer")
        return PaymentRequest.objects.create(
            requester=self.context["request"].user,
            payer=payer,
            **validated_data,
        )
