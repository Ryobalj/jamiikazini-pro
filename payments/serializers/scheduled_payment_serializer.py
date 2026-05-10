# payments/serializers/scheduled_payment_serializer.py

from rest_framework import serializers
from django.utils import timezone
from payments.models.scheduled_payment import ScheduledPayment
from payments.models.currency import Currency
from payments.models.paymentmethod import PaymentMethod

class ScheduledPaymentSerializer(serializers.ModelSerializer):
    """Serializer kamili kwa ScheduledPayment yenye validations na computed fields"""
    
    # Readable fields
    created_by_name = serializers.CharField(
        source="created_by.get_full_name",
        read_only=True
    )
    recipient_user_name = serializers.CharField(
        source="recipient_user.get_full_name",
        read_only=True
    )
    currency_code = serializers.CharField(
        source="currency.code",
        read_only=True
    )
    currency_name = serializers.CharField(
        source="currency.name",
        read_only=True
    )
    payment_method_name = serializers.CharField(
        source="payment_method.name",
        read_only=True
    )
    
    # Computed properties
    is_due = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    
    class Meta:
        model = ScheduledPayment
        fields = [
            'id',
            'amount',
            'currency',
            'currency_code',
            'currency_name',
            'payment_method',
            'payment_method_name',
            'description',
            'recipient_user',
            'recipient_user_name',
            'recipient_wallet',
            'schedule_date',
            'status',
            'payment_reference',
            'metadata',
            'executed_at',
            'cancelled_at',
            'error_message',
            'created_by',
            'created_by_name',
            'is_due',
            'can_be_cancelled',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'status',
            'payment_reference',
            'executed_at',
            'cancelled_at',
            'error_message',
            'is_due',
            'can_be_cancelled',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name',
            'recipient_user_name',
            'currency_code',
            'currency_name',
            'payment_method_name',
        ]

    def validate_schedule_date(self, value):
        """Hakikisha tarehe ya schedule ipo mbele ya sasa"""
        if value <= timezone.now():
            raise serializers.ValidationError("Tarehe ya kurasmishwa lazima iwe baada ya sasa.")
        return value

    def validate_amount(self, value):
        """Hakikisha kiasi ni sahihi"""
        if value <= 0:
            raise serializers.ValidationError("Kiasi lazima kiwe zaidi ya sifuri.")
        return value

    def validate(self, attrs):
        """Validate mpokeaji tofauti na mtumiaji anayelipa"""
        request_user = self.context['request'].user
        recipient = attrs.get('recipient_user')
        if recipient == request_user:
            raise serializers.ValidationError({
                'recipient_user': "Huwezi kujirasmishia malipo."
            })
        return attrs

    def create(self, validated_data):
        """Auto-assign created_by field"""
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)