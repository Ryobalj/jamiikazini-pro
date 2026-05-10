# jamiitasks/tasks/exchange_rate_tasks.py

import requests
import logging
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from jamiitasks.config.throttling import THROTTLE_LIMITS
from jamiitasks.utils.throttling import throttled_task
from jamiitasks.models import TaskLog  # assuming una model hii ya logging

from payments.models.currency import Currency
from payments.models.exchange_rate import ExchangeRate

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="jamiitasks.tasks.exchange_rate_tasks.update_rates_from_source",
    max_retries=3,
    default_retry_delay=300,  # Retry every 5 minutes
    rate_limit=THROTTLE_LIMITS.get(
        "jamiitasks.tasks.exchange_rate_tasks.update_rates_from_source", "1/m"
    ),
)

@throttled_task(limit=5, period=60)
def update_exchange_rates_task(self, base_code="TZS", target_code=None):
    """
    Update exchange rates with failover from BOT → OXR.
    Runs daily via Celery beat or manual trigger.
    Throttled to prevent over-fetching from APIs.
    """

    task_id = self.request.id
    log_entry = TaskLog.start(task_name=self.name, task_id=task_id, params={"base_code": base_code})
    logger.info(f"[ExchangeRate:{task_id}] Starting update for base: {base_code}")

    try:
        base_currency = Currency.objects.filter(code=base_code, is_active=True).first()
        if not base_currency:
            raise ValueError(f"Base currency {base_code} not found or inactive.")

        rates, source_used = {}, None

        # Priority 1: BOT
        try:
            rates = fetch_from_bot(base_code, target_code)
            if rates:
                source_used = "BOT"
                logger.info(f"[ExchangeRate:{task_id}] Data fetched from BOT ({len(rates)} rates).")
        except Exception as e:
            logger.warning(f"[ExchangeRate:{task_id}] BOT fetch failed: {e}")

        # Priority 2: OXR (fallback)
        if not rates:
            try:
                rates = fetch_from_oxr(base_code, target_code)
                if rates:
                    source_used = "OXR"
                    logger.info(f"[ExchangeRate:{task_id}] Data fetched from OXR ({len(rates)} rates).")
            except Exception as e2:
                raise RuntimeError(f"OXR fetch failed: {e2}")

        if not rates:
            raise RuntimeError("No rates retrieved from any source.")

        updated_count = 0
        today = timezone.now().date()

        for target, rate in rates.items():
            if target == base_code:
                continue

            target_currency = Currency.objects.filter(code=target, is_active=True).first()
            if not target_currency:
                logger.debug(f"[ExchangeRate:{task_id}] Target {target} not found, skipping.")
                continue

            try:
                rate_decimal = Decimal(str(rate))
            except (InvalidOperation, TypeError):
                logger.warning(f"[ExchangeRate:{task_id}] Invalid rate for {target}: {rate}")
                continue

            ExchangeRate.objects.update_or_create(
                base_currency=base_currency,
                target_currency=target_currency,
                effective_date=today,
                defaults={
                    "rate": rate_decimal,
                    "source": source_used,
                }
            )
            updated_count += 1

        msg = f"{updated_count} exchange rates updated successfully using {source_used}."
        logger.info(f"[ExchangeRate:{task_id}] ✅ {msg}")
        log_entry.complete(status="success", message=msg)
        return msg

    except (requests.RequestException, ValueError, RuntimeError) as e:
        logger.error(f"[ExchangeRate:{task_id}] ❌ Error: {e}", exc_info=True)
        log_entry.fail(error=str(e))
        raise self.retry(exc=e, countdown=600)  # Retry after 10 minutes

    except Exception as e:
        logger.critical(f"[ExchangeRate:{task_id}] ⚠️ Unexpected failure: {e}", exc_info=True)
        log_entry.fail(error=str(e))
        raise

    finally:
        log_entry.finalize()


def fetch_from_bot(base_code, target_code=None):
    """Fetch exchange rates from Bank of Tanzania API."""
    url = "https://www.bot.go.tz/exchange_rates.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    rates = {}
    for item in data.get("rates", []):
        code = item.get("currency_code")
        rate = item.get("rate_to_tzs")
        if not code or rate is None:
            continue
        if target_code and code != target_code:
            continue
        rates[code] = rate
    return rates


def fetch_from_oxr(base_code, target_code=None):
    """Fetch exchange rates from OpenExchangeRates."""
    api_key = getattr(settings, "OPENEXCHANGERATES_API_KEY", None)
    if not api_key:
        raise ValueError("Missing OPENEXCHANGERATES_API_KEY in settings.")

    url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}&base={base_code}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    rates = {}
    for code, value in data.get("rates", {}).items():
        if target_code and code != target_code:
            continue
        rates[code] = value
    return rates