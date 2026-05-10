# payments/serializers/exchange_rate_serializer.py

from rest_framework import serializers
from payments.models.exchange_rate import ExchangeRate
from payments.serializers.currency_serializer import CurrencySerializer


class ExchangeRateSerializer(serializers.ModelSerializer):
    base_currency = CurrencySerializer(read_only=True)
    target_currency = CurrencySerializer(read_only=True)
    base_currency_id = serializers.PrimaryKeyRelatedField(
        queryset=ExchangeRate._meta.get_field('base_currency').remote_field.model.objects.all(),
        source='base_currency',
        write_only=True
    )
    target_currency_id = serializers.PrimaryKeyRelatedField(
        queryset=ExchangeRate._meta.get_field('target_currency').remote_field.model.objects.all(),
        source='target_currency',
        write_only=True
    )

    class Meta:
        model = ExchangeRate
        fields = [
            'id', 'base_currency', 'target_currency',
            'base_currency_id', 'target_currency_id',
            'rate', 'source', 'effective_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_rate(self, value):
        """
        Hakikisha rate ni zaidi ya sifuri.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Kiwango cha ubadilishaji lazima kiwe zaidi ya sifuri."
            )
        return value

    def validate(self, attrs):
        """
        Validation ya kuhakikisha base currency na target currency siyo moja.
        """
        base_currency = attrs.get('base_currency') or getattr(self.instance, 'base_currency', None)
        target_currency = attrs.get('target_currency') or getattr(self.instance, 'target_currency', None)

        if base_currency and target_currency and base_currency == target_currency:
            raise serializers.ValidationError({
                "target_currency_id": "Sarafu ya msingi na sarafu lengwa haziwezi kuwa sawa."
            })

        return attrs