# billpay/serializers/bill_payment_serializer.py

from decimal import Decimal
from rest_framework import serializers

from billpay.models.biller import Biller
from billpay.models.bill_payment import BillPayment


class BillerSerializer(serializers.ModelSerializer):
    country_code = serializers.CharField(source="country.code", read_only=True)

    class Meta:
        model = Biller
        fields = ["id", "name", "category", "country", "country_code", "is_active"]
        read_only_fields = fields


class BillPaymentSerializer(serializers.ModelSerializer):
    biller_name = serializers.CharField(source="biller.name", read_only=True)
    biller_category = serializers.CharField(source="biller.category", read_only=True)
    currency_code = serializers.CharField(source="currency.code", read_only=True)
    token_or_receipt = serializers.SerializerMethodField()

    class Meta:
        model = BillPayment
        fields = [
            "id", "biller", "biller_name", "biller_category", "account_number",
            "amount", "currency", "currency_code", "status", "external_reference",
            "token_or_receipt", "created_at",
        ]
        read_only_fields = [
            "id", "biller_name", "biller_category", "currency_code", "status",
            "external_reference", "token_or_receipt", "created_at",
        ]

    def get_token_or_receipt(self, obj):
        return obj.token_or_receipt


class BillPaymentCreateSerializer(serializers.Serializer):
    biller = serializers.PrimaryKeyRelatedField(queryset=Biller.objects.filter(is_active=True))
    account_number = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("1"))
