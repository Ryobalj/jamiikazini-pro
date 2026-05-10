# payments/services/currency_service.py

import logging
from decimal import Decimal, InvalidOperation, DivisionByZero
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from payments.models.currency import Currency
from payments.models.exchange_rate import ExchangeRate
from security.helpers.alerts import send_slack_alert


logger = logging.getLogger(__name__)


def get_default_currency_code() -> str:
    """
    Return the system-wide default currency code (e.g., 'TZS').
    """
    return getattr(settings, "DEFAULT_CURRENCY", "TZS")


def get_currency_object(code: str) -> Currency | None:
    """
    Fetch a Currency object by code if active.
    """
    return Currency.objects.filter(code=code.upper(), is_active=True).first()


def _get_latest_rate(base: str, target: str):
    """Internal helper: fetch latest ExchangeRate."""
    return (
        ExchangeRate.objects.filter(
            base_currency__code=base,
            target_currency__code=target,
            effective_date__lte=timezone.now().date(),
        )
        .order_by("-effective_date")
        .first()
    )


def convert(amount: Decimal, from_code: str, to_code: str | None = None) -> Decimal:
    """
    Convert an amount from one currency to another.
    Enhanced v2 logic:
    - If direct rate missing, try reverse rate (1/rate).
    - If still missing, try pivot conversion using default currency.
    """
    if not to_code:
        to_code = get_default_currency_code()

    from_code = from_code.upper()
    to_code = to_code.upper()

    # No conversion needed
    if from_code == to_code:
        return Decimal(str(amount))

    # Try direct rate
    rate = _get_latest_rate(from_code, to_code)

    # Try reverse rate using 1/r
    if not rate:
        reverse = _get_latest_rate(to_code, from_code)
        if reverse:
            try:
                return Decimal(str(amount)) * (Decimal("1") / reverse.rate)
            except (InvalidOperation, DivisionByZero):
                raise ValidationError(f"Invalid reverse exchange rate for {to_code} → {from_code}")

    # Try pivot via default currency
    default = get_default_currency_code()
    if not rate and from_code != default and to_code != default:
        try:
            part1 = convert(amount, from_code, default)
            return convert(part1, default, to_code)
        except Exception as e:
            logger.warning(f"[CurrencyService] Pivot conversion failed: {from_code} → {default} → {to_code}")
            raise ValidationError(str(e))

    if not rate:
        logger.warning(f"[CurrencyService] Missing exchange rate: {from_code} → {to_code}")
        raise ValidationError(f"No exchange rate available from {from_code} to {to_code}")

    # Calculate
    try:
        return Decimal(str(amount)) * rate.rate
    except (InvalidOperation, TypeError):
        raise ValidationError(f"Invalid amount: {amount}")


def convert_to_default(amount: Decimal, currency: str, base_currency: str = None) -> Decimal:
    """
    Convert to default currency.
    Enhanced v2:
    - Try reverse rate if needed.
    - Try pivot through default currency.
    """
    if not base_currency:
        base_currency = getattr(settings, "DEFAULT_CURRENCY", "TZS")

    currency = currency.upper()
    base_currency = base_currency.upper()

    if currency == base_currency:
        return Decimal(str(amount))

    try:
        # Direct rate
        rate = _get_latest_rate(currency, base_currency)

        # Try reverse
        if not rate:
            reverse = _get_latest_rate(base_currency, currency)
            if reverse:
                return Decimal(amount) * (Decimal("1") / reverse.rate)

        # Try pivot via default
        default = get_default_currency_code()
        if not rate and currency != default and base_currency != default:
            part1 = convert(amount, currency, default)
            return convert(part1, default, base_currency)

        if not rate:
            send_slack_alert(
                f"[Currency Service] No exchange rate found for {currency} → {base_currency}"
            )
            raise ValueError(f"No exchange rate for {currency} → {base_currency}")

        return Decimal(amount) * rate.rate

    except Exception as e:
        send_slack_alert(
            f"[Currency Service] Conversion failed: {currency} → {base_currency}, amount={amount}, error={e}"
        )
        raise