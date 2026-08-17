# logistics/management/commands/seed_transport_rate_cards.py

from django.core.management.base import BaseCommand
from logistics.choices import TransportTypeChoices
from logistics.models.rate_card import TransportRateCard

# Kiwango cha awali cha bei (TZS): base_fare + per_km_rate*distance_km +
# per_kg_rate*weight_kg, na kima cha chini (minimum_fare). Vinaweza
# kubadilishwa baadaye na admin bila deploy.
#
# boda_boda, public_transport, na bus zimekokotolewa moja kwa moja kulingana
# na bei halisi za sokoni: boda_boda ~TSh 2000-3000 kwa mzigo wa kg 50-80 na
# umbali wa km 2; daladala ~TSh 2000-3000 kwa km 30-40; basi la mikoani
# ~TSh 5000-7000 kwa mzigo wa kg 30 na umbali wa km 700. Vyombo vya usafiri
# wa umma (daladala/bus) havikodishwi kwa ajili ya mzigo pekee - mzigo mdogo
# "unapanda" pamoja na abiria, hivyo per_kg_rate=0 kwa hivyo (bei inategemea
# umbali tu, si uzito, ndani ya kikomo kidogo cha uzito - angalia weight_bands.py).
RATES = {
    TransportTypeChoices.BICYCLE: {"base_fare": 500, "per_km_rate": 200, "per_kg_rate": 10, "minimum_fare": 800},
    TransportTypeChoices.BODA_BODA: {"base_fare": 1000, "per_km_rate": 300, "per_kg_rate": 15, "minimum_fare": 1500},
    TransportTypeChoices.BAJAJI: {"base_fare": 1300, "per_km_rate": 350, "per_kg_rate": 8, "minimum_fare": 1800},
    TransportTypeChoices.TAXI: {"base_fare": 2000, "per_km_rate": 500, "per_kg_rate": 10, "minimum_fare": 3000},
    TransportTypeChoices.SUZUKI_CARRY: {"base_fare": 5000, "per_km_rate": 700, "per_kg_rate": 8, "minimum_fare": 7000},
    TransportTypeChoices.TUK_TUK: {"base_fare": 1500, "per_km_rate": 400, "per_kg_rate": 5, "minimum_fare": 2000},
    TransportTypeChoices.PUBLIC_TRANSPORT: {"base_fare": 1000, "per_km_rate": 43, "per_kg_rate": 0, "minimum_fare": 2000},
    TransportTypeChoices.BUS: {"base_fare": 1500, "per_km_rate": 6.5, "per_kg_rate": 0, "minimum_fare": 3000},
    TransportTypeChoices.CANTER: {"base_fare": 15000, "per_km_rate": 1200, "per_kg_rate": 5, "minimum_fare": 20000},
    TransportTypeChoices.FUSO: {"base_fare": 30000, "per_km_rate": 2000, "per_kg_rate": 3, "minimum_fare": 40000},
    TransportTypeChoices.SCANIA: {"base_fare": 60000, "per_km_rate": 3500, "per_kg_rate": 2, "minimum_fare": 80000},
    TransportTypeChoices.TRAIN: {"base_fare": 20000, "per_km_rate": 800, "per_kg_rate": 2, "minimum_fare": 25000},
    TransportTypeChoices.SHIP: {"base_fare": 50000, "per_km_rate": 1000, "per_kg_rate": 1, "minimum_fare": 60000},
    TransportTypeChoices.AIR: {"base_fare": 100000, "per_km_rate": 5000, "per_kg_rate": 50, "minimum_fare": 150000},
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
