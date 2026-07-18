# logistics/management/commands/seed_transport_rate_cards.py

from django.core.management.base import BaseCommand
from logistics.choices import TransportTypeChoices
from logistics.models.rate_card import TransportRateCard

# Kiwango cha awali cha bei (TZS) - base_fare + per_km_rate*distance_km, na kima
# cha chini (minimum_fare). Vinaweza kubadilishwa baadaye na admin bila deploy.
RATES = {
    TransportTypeChoices.BODA_BODA: {"base_fare": 1000, "per_km_rate": 300, "minimum_fare": 1500},
    TransportTypeChoices.BAJAJI: {"base_fare": 1300, "per_km_rate": 350, "minimum_fare": 1800},
    TransportTypeChoices.SUZUKI_CARRY: {"base_fare": 5000, "per_km_rate": 700, "minimum_fare": 7000},
    TransportTypeChoices.TUK_TUK: {"base_fare": 1500, "per_km_rate": 400, "minimum_fare": 2000},
    TransportTypeChoices.PUBLIC_TRANSPORT: {"base_fare": 2000, "per_km_rate": 500, "minimum_fare": 3000},
    TransportTypeChoices.BUS: {"base_fare": 8000, "per_km_rate": 900, "minimum_fare": 10000},
    TransportTypeChoices.CANTER: {"base_fare": 15000, "per_km_rate": 1200, "minimum_fare": 20000},
    TransportTypeChoices.FUSO: {"base_fare": 30000, "per_km_rate": 2000, "minimum_fare": 40000},
    TransportTypeChoices.SCANIA: {"base_fare": 60000, "per_km_rate": 3500, "minimum_fare": 80000},
    TransportTypeChoices.TRAIN: {"base_fare": 20000, "per_km_rate": 800, "minimum_fare": 25000},
    TransportTypeChoices.SHIP: {"base_fare": 50000, "per_km_rate": 1000, "minimum_fare": 60000},
    TransportTypeChoices.AIR: {"base_fare": 100000, "per_km_rate": 5000, "minimum_fare": 150000},
}


class Command(BaseCommand):
    help = "Seed TransportRateCard rows for every TransportTypeChoices vehicle type."

    def handle(self, *args, **options):
        created, updated = 0, 0
        for vehicle_type, rates in RATES.items():
            obj, was_created = TransportRateCard.objects.update_or_create(
                vehicle_type=vehicle_type,
                defaults=rates,
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"TransportRateCard: {created} created, {updated} updated."))
