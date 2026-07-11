# payments/management/commands/update_exchange_rates.py

import requests
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from payments.models.currency import Currency
from payments.models.exchange_rate import ExchangeRate
from django.conf import settings


class Command(BaseCommand):
    help = "Update exchange rates from Bank of Tanzania or fallback API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--base",
            type=str,
            help="Base currency code (default: TZS)",
        )
        parser.add_argument(
            "--target",
            type=str,
            help="Target currency code (optional: update only this pair)",
        )
        parser.add_argument(
            "--source",
            type=str,
            default="ERAPI",
            choices=["ERAPI", "BOT", "OXR"],
            help="Source API: ERAPI (exchangerate-api.com, free/no key), "
                 "BOT (Bank of Tanzania) or OXR (OpenExchangeRates).",
        )

    def handle(self, *args, **options):
        base_code = options["base"] or "TZS"
        target_code = options["target"]
        source = options["source"]

        base_currency = Currency.objects.filter(code=base_code, is_active=True).first()
        if not base_currency:
            raise CommandError(f"Base currency {base_code} not found or inactive.")

        self.stdout.write(self.style.NOTICE(f"Updating exchange rates from {source}..."))

        try:
            if source == "ERAPI":
                rates = self.fetch_from_erapi(base_code, target_code)
            elif source == "BOT":
                rates = self.fetch_from_bot(base_code, target_code)
            else:
                rates = self.fetch_from_oxr(base_code, target_code)
        except Exception as e:
            raise CommandError(f"Failed to fetch rates: {e}")

        updated_count = 0
        for target, rate in rates.items():
            if target == base_code:
                continue
            target_currency = Currency.objects.filter(code=target, is_active=True).first()
            if not target_currency:
                self.stdout.write(self.style.WARNING(f"Target currency {target} not found, skipping."))
                continue

            exchange_rate, created = ExchangeRate.objects.update_or_create(
                base_currency=base_currency,
                target_currency=target_currency,
                effective_date=timezone.now().date(),
                defaults={
                    "rate": Decimal(str(rate)),
                    "source": source,
                }
            )
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} exchange rates."))

    def fetch_from_erapi(self, base_code, target_code=None):
        """
        exchangerate-api.com "open" endpoint — free, no API key, rates halisi
        za soko (zinasasishwa kila siku). https://www.exchangerate-api.com/docs/free
        """
        url = f"https://open.er-api.com/v6/latest/{base_code}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("result") != "success":
            raise CommandError(f"ERAPI error: {data.get('error-type', 'unknown')}")

        rates = {}
        for code, value in data.get("rates", {}).items():
            if target_code and code != target_code:
                continue
            rates[code] = value
        return rates

    def fetch_from_bot(self, base_code, target_code=None):
        """
        Example Bank of Tanzania API endpoint.
        Note: This is a mock. Replace with actual endpoint and parsing.
        """
        url = "https://www.bot.go.tz/exchange_rates.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Example structure — adjust based on actual BOT API response
        rates = {}
        for item in data.get("rates", []):
            code = item["currency_code"]
            if target_code and code != target_code:
                continue
            rates[code] = item["rate_to_tzs"]
        return rates

    def fetch_from_oxr(self, base_code, target_code=None):
        """
        OpenExchangeRates API
        """
        api_key = getattr(settings, "OPENEXCHANGERATES_API_KEY", None)
        if not api_key:
            raise CommandError("Missing OPENEXCHANGERATES_API_KEY in settings.")

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