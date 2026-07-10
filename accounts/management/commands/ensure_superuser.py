"""
Unda superuser bila mwingiliano (non-interactive) kutoka env vars.

Muhimu kwa Render free tier ambayo HAINA Shell tab, kwa hivyo `createsuperuser`
ya kawaida (interactive) haiwezekani. Command hii ni idempotent — ikiitwa mara
nyingi (kila deploy) haileti kosa; inaunda tu ikiwa superuser hayupo.

Env vars zinazotumika:
  DJANGO_SUPERUSER_EMAIL       (lazima)
  DJANGO_SUPERUSER_PASSWORD    (lazima)
  DJANGO_SUPERUSER_FULL_NAME   (hiari, default "Admin")
"""

import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Unda superuser kutoka env vars ikiwa hayupo (idempotent, non-interactive)."

    def handle(self, *args, **options):
        User = get_user_model()

        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
        full_name = os.getenv("DJANGO_SUPERUSER_FULL_NAME", "Admin")

        if not email or not password:
            self.stdout.write(
                "DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD hazijawekwa "
                "— naruka uundaji wa superuser."
            )
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(f"Superuser '{email}' tayari yupo — naruka.")
            return

        User.objects.create_superuser(
            email=email,
            password=password,
            full_name=full_name,
        )
        self.stdout.write(self.style.SUCCESS(f"Superuser '{email}' ameundwa."))
