# billpay/management/commands/seed_billers.py

from django.core.management.base import BaseCommand

from gov_integration.models.country_config import CountryConfig
from billpay.models.biller import Biller, BillerCategory

BILLERS = [
    {"country": "TZ", "config_key": "TZ_LUKU", "category": BillerCategory.ELECTRICITY, "name": "LUKU (TANESCO)"},
    {"country": "TZ", "config_key": "TZ_AIRTIME", "category": BillerCategory.AIRTIME, "name": "Muda wa Maongezi"},
    {"country": "TZ", "config_key": "TZ_DSTV", "category": BillerCategory.TV, "name": "DSTV/GOtv"},
    {"country": "TZ", "config_key": "TZ_WATER", "category": BillerCategory.WATER, "name": "DAWASA"},
    {"country": "KE", "config_key": "KE_KPLC", "category": BillerCategory.ELECTRICITY, "name": "KPLC"},
    {"country": "KE", "config_key": "KE_AIRTIME", "category": BillerCategory.AIRTIME, "name": "Muda wa Maongezi"},
    {"country": "UG", "config_key": "UG_UMEME", "category": BillerCategory.ELECTRICITY, "name": "UMEME"},
    {"country": "UG", "config_key": "UG_AIRTIME", "category": BillerCategory.AIRTIME, "name": "Muda wa Maongezi"},
    {"country": "RW", "config_key": "RW_EUCL", "category": BillerCategory.ELECTRICITY, "name": "EUCL"},
    {"country": "RW", "config_key": "RW_AIRTIME", "category": BillerCategory.AIRTIME, "name": "Muda wa Maongezi"},
]


class Command(BaseCommand):
    help = "Seed the standard Biller records (LUKU, airtime, DSTV, water) per country."

    def handle(self, *args, **options):
        created_count = 0
        for entry in BILLERS:
            country, _ = CountryConfig.objects.get_or_create(
                code=entry["country"],
                defaults={"name": dict(CountryConfig.ISO_CODES).get(entry["country"], entry["country"])},
            )
            _, created = Biller.objects.get_or_create(
                country=country,
                config_key=entry["config_key"],
                defaults={"name": entry["name"], "category": entry["category"]},
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded billers: {created_count} created, {len(BILLERS) - created_count} already existed."))
