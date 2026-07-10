# jamiiwallet/serializers/topup_serializer.py

from rest_framework import serializers
from jamiiwallet.models.topup import TopUp
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.wallet import Wallet


class TopUpSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    # channel ni ya lazima kimuundo (bila hii, confirm hukwama "Unknown payment channel '').
    # Default = PAWAPAY (sawa na frontend), kwa hivyo topup haitawahi kuwa na channel tupu.
    channel = serializers.ChoiceField(
        choices=TopUp.TopUpChannel.choices,
        required=False,
        default=TopUp.TopUpChannel.PAWAPAY,
    )
    reference = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = TopUp
        fields = ['id', 'amount', 'channel', 'reference', 'status', 'created_at']
        read_only_fields = ['id', 'reference', 'status', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def create(self, validated_data):
        # TopUp is user-based; the view queues the confirmation task itself.
        validated_data.setdefault("user", self.context["request"].user)
        return TopUp.objects.create(**validated_data)