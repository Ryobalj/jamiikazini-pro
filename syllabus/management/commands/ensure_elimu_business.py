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
ELIMU_BUSINESS_NAME = "JamiiShule"
# Renamed from "Jamiikazini Elimu" on 2026-08-19 - kept here so a stray old
# row (from before the rename) can be found and renamed in place instead of
# get_or_create spawning a duplicate business under the new name.
ELIMU_BUSINESS_NAME_LEGACY = "Jamiikazini Elimu"

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
    {
        "name": "Jaribio/Mtihani (Quiz)",
        "description": (
            "Zana ya kutengeneza jaribio, mtihani wa mazoezi au mtihani "
            "moja kwa moja kutoka kwa muhtasari rasmi, ikiwa na maswali "
            "yaliyopangwa kwa kiwango cha ugumu na mwongozo wa majibu."
        ),
        "external_link": "/teaching/quiz",
    },
]


class Command(BaseCommand):
    help = (
        "Hakikisha Business 'JamiiShule' (na bidhaa zake) ipo, ikiundwa "
        "kiotomatiki mara ya kwanza tu ikiwa haipo (na kubadili jina la "
        "rekodi ya zamani 'Jamiikazini Elimu' ikiwa ipo). Haigusi/kubadili "
        "data nyingine iliyopo (get_or_create pekee), hivyo ni salama "
        "kuiendesha kwenye kila deploy."
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

        # A row from before the 2026-08-19 rename may still exist under the
        # legacy name - rename it in place rather than letting
        # get_or_create spawn a duplicate "JamiiShule" business.
        legacy = Business.objects.filter(owner=owner, name=ELIMU_BUSINESS_NAME_LEGACY).first()
        if legacy is not None:
            legacy.name = ELIMU_BUSINESS_NAME
            legacy.save(update_fields=["name"])
            self.stdout.write(self.style.SUCCESS(
                f"Imebadilishwa jina: '{ELIMU_BUSINESS_NAME_LEGACY}' -> '{ELIMU_BUSINESS_NAME}' ({legacy.id})"
            ))

        business, created = Business.objects.get_or_create(
            owner=owner,
            name=ELIMU_BUSINESS_NAME,
            defaults=dict(
                category=category,
                email=owner.email,
                description=(
                    "Zana za kidijitali zinazomsaidia mwalimu kuandaa nyaraka "
                    "zake za kazi (Azimio la Kazi, Andalio la Somo, majaribio) "
                    "moja kwa moja kutoka kwa muhtasari rasmi wa TET."
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
            # get_or_create's defaults only apply on creation - a
            # pre-rename row needs its description refreshed explicitly.
            new_description = (
                "Zana za kidijitali zinazomsaidia mwalimu kuandaa nyaraka "
                "zake za kazi (Azimio la Kazi, Andalio la Somo, majaribio) "
                "moja kwa moja kutoka kwa muhtasari rasmi wa TET."
            )
            if business.description != new_description:
                business.description = new_description
                business.save(update_fields=["description"])

        currency = self._get_tzs_currency()
        products_created = 0
        products = []
        for spec in ELIMU_PRODUCTS:
            product, product_created = Product.objects.get_or_create(
                business=business,
                name=spec["name"],
                defaults=dict(
                    description=spec["description"],
                    type=ProductType.DIGITAL,
                    price=self._get_monthly_fee(),
                    currency=currency,
                    is_available=True,
                    is_featured=True,
                    language_code="sw",
                    external_link=spec["external_link"],
                ),
            )
            if not product_created and not product.is_featured:
                # get_or_create's defaults only apply on creation - an
                # already-existing row needs is_featured set explicitly.
                product.is_featured = True
                product.save(update_fields=["is_featured"])
            products.append(product)
            if product_created:
                products_created += 1

        if products_created:
            self.stdout.write(self.style.SUCCESS(
                f"Imeundwa bidhaa {products_created} mpya za '{business.name}'."
            ))
        else:
            self.stdout.write(f"Bidhaa za '{business.name}' tayari zipo.")

        self._ensure_featured_listings(business, products)

    def _ensure_featured_listings(self, business, products):
        """JamiiShule is the platform's own storefront, not a paying
        advertiser - its products get a standing, no-cost 'Sponsored Ads'
        placement (amount=0, no invoice) rather than going through the
        normal pay-to-feature flow every other business uses."""
        from datetime import timedelta
        from django.utils import timezone
        from decimal import Decimal
        from businesses.models.featured_listing import FeaturedListing

        today = timezone.now().date()
        far_future = today + timedelta(days=365 * 5)
        created = 0
        for product in products:
            _, was_created = FeaturedListing.objects.get_or_create(
                business=business,
                product=product,
                defaults=dict(
                    start_date=today,
                    end_date=far_future,
                    amount=Decimal("0.00"),
                    is_active=True,
                ),
            )
            if was_created:
                created += 1
        if created:
            self.stdout.write(self.style.SUCCESS(
                f"Imeundwa FeaturedListing {created} mpya za '{business.name}'."
            ))

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
