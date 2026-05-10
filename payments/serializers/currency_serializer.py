# payments/serializers/currency_serializer.py

from rest_framework import serializers
from payments.models.currency import Currency


class CurrencySerializer(serializers.ModelSerializer):
    """
    Serializer ya Currency — inaruhusu kusoma na kuunda currencies
    huku ikihakikisha fields zinazojazwa automatically hazibadilishwi na client.
    """

    # override default ChoiceField
    code = serializers.CharField()

    class Meta:
        model = Currency
        fields = [
            "id",
            "code",
            "name",
            "symbol",
            "country",
            "is_active",
            "exchange_rate_to_tzs",
        ]
        read_only_fields = ["id", "name", "symbol", "country"]

    def validate_code(self, value):
        """
        Hakikisha code ipo kwenye list ya ISO codes zilizowekwa (CURRENCY_CHOICES).
        """
        valid_codes = [choice[0] for choice in Currency.CURRENCY_CHOICES]
        if value not in valid_codes:
            raise serializers.ValidationError(
                f"Invalid currency code '{value}'. Allowed codes are: {', '.join(valid_codes)}"
            )
        return value