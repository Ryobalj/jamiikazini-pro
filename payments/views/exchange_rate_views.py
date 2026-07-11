# payments/views/exchange_rate_views.py

import logging

from django.utils import timezone

from payments.models.exchange_rate import ExchangeRate
from payments.serializers.exchange_rate_serializer import ExchangeRateSerializer
from payments.views.base import BaseCRUDViewSet

logger = logging.getLogger(__name__)


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

    def list(self, request, *args, **kwargs):
        # Hakuna Celery beat/worker kwenye free tier — sasisha rates halisi
        # za soko (ERAPI) papo hapo ikiwa hazijasasishwa leo. Task inaendesha
        # kwa usalama (EAGER mode = sync) na haiathiri jibu ikishindwa.
        self._refresh_if_stale()
        return super().list(request, *args, **kwargs)

    def _refresh_if_stale(self):
        today = timezone.now().date()
        if ExchangeRate.objects.filter(effective_date=today).exists():
            return
        try:
            from jamiitasks.tasks.exchange_rate_tasks import update_exchange_rates_task
            update_exchange_rates_task.delay(base_code="TZS")
        except Exception:
            logger.warning("Exchange rate lazy-refresh failed", exc_info=True)