# jamiiwallet/serializers/topup_serializer.py

from rest_framework import serializers
from jamiiwallet.models.topup import TopUp
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.wallet import Wallet


class TopUpSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    reference = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = TopUp
        fields = ['id', 'amount', 'reference', 'status', 'created_at']
        read_only_fields = ['id', 'reference', 'status', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        wallet = Wallet.objects.get(user=user)

        topup = TopUp.objects.create(
            wallet=wallet,
            amount=validated_data['amount']
        )

        # Delay task to process the transaction
        from jamiitasks.tasks.wallet import confirm_topup_transaction
        confirm_topup_transaction.delay(topup.id)

        return topup