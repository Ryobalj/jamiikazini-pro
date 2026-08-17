# syllabus/management/commands/ensure_elimu_business.py

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from businesses.models.product import Product, ProductType

logger = logging.getLogger(__name__)

ELIMU_CATEGORY_SLUG = "education"
ELIMU_BUSINESS_NAME = "Jamiikazini Elimu"

# Bidhaa (tools) zinazotolewa na Jamiikazini Elimu kwa sasa. Bei ni ya
# kumbukumbu tu (inaonesha thamani ya huduma) - malipo halisi hupitia
# TeacherSubscription + JamiiWallet, si Product hii moja kwa moja. Zote ni
# DIGITAL (si physical) hivyo hazina stock - `external_link` ni njia ya
# ndani (route) inayoanzisha mchakato mzima wa kupata huduma husika
# (usajili wa workstation -> usajili wa malipo -> matumizi ya zana).
ELIMU_PRODUCTS = [
    {
        "name": "Azimio la Kazi (Scheme of Work)",
        "description": (
            "Zana ya kuzalisha Azimio la Kazi (scheme of work) moja kwa moja "
            "kutoka kwa muhtasari (syllabus) rasmi wa TET, kwa somo na darasa "
            "lolote ulilonalo."
        ),
        "external_link": "/teaching/scheme",
    },
    {
        "name": "Andalio la Somo (Lesson Plan)",
        "description": (
            "Zana ya kuzalisha Andalio la Somo na Nukuu za Somo moja kwa moja "
            "kutoka kwa Azimio la Kazi, ikiwa na muda, hatua za ufundishaji, na "
            "maudhui kamili."
        ),
        "external_link": "/teaching/lesson-plan",
    },
    {
        "name": "Ratiba ya Vipindi (Timetable)",
        "description": (
            "Zana ya kumsaidia mwalimu kuunda ratiba ya vipindi ya darasa lake "
            "na kupata ratiba kuu ya shule nzima, ikiwa na siku, muda na "
            "walimu wenzake, tayari kwa kupakuliwa kama PDF."
        ),
        "external_link": "/teaching/timetable",
    },
    {
        "name": "Matokeo ya Mtihani (Exam Results)",
        "description": (
            "Zana ya kuandaa na kutoa matokeo ya mtihani kwa somo moja au "
            "kwa masomo yote ya darasa, ikiwa na daraja, wastani na nafasi, "
            "tayari kwa kupakuliwa kama PDF."
        ),
        "external_link": "/teaching/exam-results",
    },
]


class Command(BaseCommand):
    help = (
        "Hakikisha Business 'Jamiikazini Elimu' (na bidhaa zake) ipo, "
        "ikiundwa kiotomatiki mara ya kwanza tu ikiwa haipo. Haigusi/kubadili "
        "data iliyopo (get_or_create pekee), hivyo ni salama kuiendesha kwenye "
        "kila deploy."
    )

    def handle(self, *args, **options):
        owner = self._get_owner()
        if owner is None:
            self.stdout.write(self.style.WARNING(
                "PLATFORM_REVENUE_OWNER_EMAIL haijawekwa au user wake haipo bado - "
                "kuruka uundaji wa 'Jamiikazini Elimu' kwa mzunguko huu."
            ))
            return

        category = BusinessCategory.objects.filter(slug=ELIMU_CATEGORY_SLUG).first()
        if category is None:
            self.stdout.write(self.style.WARNING(
                f"Kategoria yenye slug '{ELIMU_CATEGORY_SLUG}' haipo bado "
                "(endesha seed_business_categories kwanza) - kuruka kwa mzunguko huu."
            ))
            return

        business, created = Business.objects.get_or_create(
            owner=owner,
            name=ELIMU_BUSINESS_NAME,
            defaults=dict(
                category=category,
                email=owner.email,
                description=(
                    "Zana za kidijitali zinazomsaidia mwalimu kuandaa nyaraka "
                    "zake za kazi (Azimio la Kazi, Andalio la Somo) moja kwa "
                    "moja kutoka kwa muhtasari rasmi wa TET."
                ),
                website="/teaching",
                is_active=True,
                is_verified=True,
            ),
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f"Imeundwa: Business '{business.name}' ({business.id})"
            ))
        else:
            self.stdout.write(f"Tayari ipo: Business '{business.name}' ({business.id})")

        currency = self._get_tzs_currency()
        products_created = 0
        for spec in ELIMU_PRODUCTS:
            _, product_created = Product.objects.get_or_create(
                business=business,
                name=spec["name"],
                defaults=dict(
                    description=spec["description"],
                    type=ProductType.DIGITAL,
                    price=self._get_monthly_fee(),
                    currency=currency,
                    is_available=True,
                    language_code="sw",
                    external_link=spec["external_link"],
                ),
            )
            if product_created:
                products_created += 1

        if products_created:
            self.stdout.write(self.style.SUCCESS(
                f"Imeundwa bidhaa {products_created} mpya za '{business.name}'."
            ))
        else:
            self.stdout.write(f"Bidhaa za '{business.name}' tayari zipo.")

    @staticmethod
    def _get_owner():
        User = get_user_model()
        email = getattr(settings, "PLATFORM_REVENUE_OWNER_EMAIL", "")
        if not email:
            return None
        return User.objects.filter(email=email).first()

    @staticmethod
    def _get_tzs_currency():
        from payments.models.currency import Currency
        return Currency.objects.filter(code="TZS").first()

    @staticmethod
    def _get_monthly_fee():
        from syllabus.models.teacher_subscription import TeacherSubscription
        return TeacherSubscription._meta.get_field("monthly_fee").default
