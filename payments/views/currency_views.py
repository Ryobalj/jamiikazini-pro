# payments/views/currency_views.py

from payments.models.currency import Currency
from payments.serializers.currency_serializer import CurrencySerializer
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

class CurrencyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset kwa currencies.
    - Public access, no authentication required
    """
    queryset = Currency.objects.filter(is_active=True)
    serializer_class = CurrencySerializer
    permission_classes = [AllowAny]  # ✅ Public access - NO 2FA
    filterset_fields = ["code", "country", "is_active"]
    ordering_fields = ["code", "name", "exchange_rate_to_tzs"]
    ordering = ["code"]