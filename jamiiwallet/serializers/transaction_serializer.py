# jamiiwallet/serializers/transaction_serializer.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, ROUND_DOWN

from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.wallet import Wallet


class TransactionSerializer(serializers.ModelSerializer):
    counterparty_name = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        # NB: Transaction haina field 'description' - tumia 'metadata' kwa data ya ziada
        fields = [
            'id', 'wallet', 'counterparty', 'counterparty_name', 'direction',
            'transaction_type', 'amount', 'metadata', 'status', 'reference',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'reference', 'created_at', 'updated_at']

    def get_counterparty_name(self, obj):
        return obj.counterparty.full_name if obj.counterparty_id else None

    def get_direction(self, obj):
        """'in' kama wallet ya mtumiaji huyu imeongezeka, 'out' ikipungua.
        Kwa TRANSFER, rekodi ya mtumaji ina initiated_by == mmiliki wa wallet
        (ni 'out'); rekodi ya mpokeaji ina initiated_by == mtumaji, si mmiliki
        wa wallet hiyo (ni 'in') - hii ni sahihi bila kutegemea request.user."""
        if obj.transaction_type in [Transaction.TransactionType.TOP_UP, Transaction.TransactionType.REFUND]:
            return "in"
        if obj.transaction_type == Transaction.TransactionType.WITHDRAWAL:
            return "out"
        if obj.transaction_type == Transaction.TransactionType.TRANSFER and obj.wallet_id:
            return "out" if obj.initiated_by_id == obj.wallet.user_id else "in"
        return None

    def validate(self, attrs):
        transaction_type = attrs.get('transaction_type')
        wallet = attrs.get('wallet')
        counterparty = attrs.get('counterparty')
        amount = attrs.get('amount')
        request = self.context.get('request')

        if amount <= 0:
            raise serializers.ValidationError(_('Amount must be greater than zero.'))

        # Ensure only wallet owner or superuser can initiate
        if request and request.user != wallet.user and not request.user.is_superuser:
            raise serializers.ValidationError(_('You do not own this wallet.'))

        if transaction_type in [
            Transaction.TransactionType.TRANSFER,
            Transaction.TransactionType.PAYMENT
        ]:
            if not counterparty:
                raise serializers.ValidationError(_('Counterparty is required for this transaction type.'))
            if counterparty == wallet:
                raise serializers.ValidationError(_('Cannot perform transaction to the same wallet.'))

        if transaction_type in [
            Transaction.TransactionType.TRANSFER,
            Transaction.TransactionType.WITHDRAWAL
        ]:
            if wallet.balance < amount:
                raise serializers.ValidationError(_('Insufficient wallet balance.'))

        return attrs

    def create(self, validated_data):
        """
        This assumes the actual wallet balance operations and status changes
        will be handled in a dedicated transaction processor/service layer
        to ensure consistency, logging, and concurrency safety.
        """
        # Pre-round amount to two decimal places
        amount = validated_data['amount'].quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        validated_data['amount'] = amount

        transaction = Transaction.objects.create(**validated_data)

        # Actual balance update logic should be done in the transaction service/processor
        return transaction
