# payments/views/exchange_rate_views.py

from payments.models.exchange_rate import ExchangeRate
from payments.serializers.exchange_rate_serializer import ExchangeRateSerializer
from payments.views.base import BaseCRUDViewSet

class ExchangeRateViewSet(BaseCRUDViewSet):
    """
    CRUD viewset kwa ExchangeRate.
    - base_currency na target_currency ni read-only kwa display.
    - Tumia base_currency_id na target_currency_id kwa write.
    """
    queryset = ExchangeRate.objects.select_related('base_currency', 'target_currency')
    serializer_class = ExchangeRateSerializer
    filterset_fields = ['base_currency', 'target_currency', 'effective_date']
    ordering_fields = ['effective_date', 'rate']
    ordering = ['-effective_date']