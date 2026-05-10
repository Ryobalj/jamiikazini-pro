# payments/serializers/payment_link_serializer.py

from rest_framework import serializers
from django.utils import timezone
from payments.models.payment_link import PaymentLink
from payments.models.currency import Currency


class PaymentLinkSerializer(serializers.ModelSerializer):
    """Serializer kamili kwa PaymentLink"""
    
    # Readable fields
    created_by_name = serializers.CharField(
        source="created_by.get_full_name",
        read_only=True
    )
    used_by_name = serializers.CharField(
        source="used_by.get_full_name",
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
    
    # Computed properties
    is_expired = serializers.ReadOnlyField()
    is_usable = serializers.ReadOnlyField()
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = PaymentLink
        fields = [
            'id',
            'link_code',
            'amount',
            'currency',
            'currency_code',
            'currency_name',
            'description',
            'expires_at',
            'status',
            'created_by',
            'created_by_name',
            'used_by',
            'used_by_name',
            'used_at',
            'payment_reference',
            'metadata',
            'allowed_methods',
            'is_expired',
            'is_usable',
            'absolute_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'status',
            'used_by',
            'used_at',
            'payment_reference',
            'created_at',
            'updated_at',
            'is_expired',
            'is_usable',
            'absolute_url',
        ]

    def get_absolute_url(self, obj):
        """Rudisha URL kamili ya kiungo"""
        return obj.get_absolute_url()

    def validate_expires_at(self, value):
        """Hakikisha tarehe ya kumalizika ipo mbele ya sasa"""
        if value <= timezone.now():
            raise serializers.ValidationError("Tarehe ya kumalizika lazima iwe baada ya sasa.")
        return value

    def validate_amount(self, value):
        """Hakikisha kiasi ni sahihi"""
        if value <= 0:
            raise serializers.ValidationError("Kiasi lazima kiwe zaidi ya sifuri.")
        return value

    def create(self, validated_data):
        """Unda PaymentLink mpya"""
        user = self.context['request'].user
        validated_data['created_by'] = user
        
        # Ikiwa hakuna allowed_methods, weka default
        if 'allowed_methods' not in validated_data or not validated_data['allowed_methods']:
            validated_data['allowed_methods'] = ['wallet', 'mobile_money']
        
        return super().create(validated_data)