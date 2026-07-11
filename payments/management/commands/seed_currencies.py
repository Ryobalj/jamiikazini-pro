# payments/management/commands/seed_currencies.py

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.models.currency import Currency
from payments.models.exchange_rate import ExchangeRate

# Viwango vya awali (TZS -> target). Vinafanana na fallback ya frontend
# (CurrencyContext.jsx) ili mtumiaji asione mabadiliko makubwa ghafla.
# Zinaweza kusasishwa baadaye na `update_exchange_rates` (BOT/OXR) mara
# chanzo halisi cha data kitakapowekwa.
SEED_RATES_FROM_TZS = {
    "KES": Decimal("0.047"),
    "UGX": Decimal("28"),
    "RWF": Decimal("0.83"),
    "BIF": Decimal("0.87"),
    "USD": Decimal("0.00037"),
    "EUR": Decimal("0.00034"),
    "GBP": Decimal("0.00029"),
}


class Command(BaseCommand):
    help = "Seed Currency records + initial ExchangeRate (TZS base) — idempotent."

    def handle(self, *args, **options):
        codes = ["TZS"] + list(SEED_RATES_FROM_TZS.keys())
        currencies = {}
        for code in codes:
            currency, created = Currency.objects.get_or_create(code=code, defaults={"is_active": True})
            currencies[code] = currency
            if created:
                self.stdout.write(self.style.SUCCESS(f"Currency created: {code}"))

        base = currencies["TZS"]
        today = timezone.now().date()
        count = 0
        for code, rate in SEED_RATES_FROM_TZS.items():
            _, created = ExchangeRate.objects.get_or_create(
                base_currency=base,
                target_currency=currencies[code],
                effective_date=today,
                defaults={"rate": rate, "source": "SEED"},
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {count} exchange rates (TZS base)."))
