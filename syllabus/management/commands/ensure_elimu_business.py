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

# JamiiShule's first product: ONE subscription covering every teaching
# tool (Scheme of Work, Lesson Plan, Timetable, Exam Results, Quiz - all
# listed inside /teaching itself), not five separate storefront listings.
# Bei ni ya kumbukumbu tu (inaonesha thamani ya huduma) - malipo halisi
# hupitia TeacherSubscription + JamiiWallet, si Product hii moja kwa moja.
TEACHING_SERVICES_PRODUCT = {
    "name": "Huduma za Kufundishia (Teaching Services)",
    "description": (
        "Usajili mmoja unaomsaidia mwalimu kupata zana zote za kufundishia "
        "moja kwa moja kutoka kwa muhtasari rasmi wa TET: Azimio la Kazi, "
        "Andalio la Somo, Ratiba ya Vipindi, Matokeo ya Mtihani, na "
        "Majaribio/Mitihani."
    ),
    "external_link": "/teaching",
}

# Names this business used to list as five separate products (one per
# tool), before they were collapsed into the single subscription product
# above - kept here only so a prior deploy's rows (and their standing
# FeaturedListings, which cascade-delete with the product) can be cleaned
# up automatically rather than lingering as stale duplicate listings.
LEGACY_PER_TOOL_PRODUCT_NAMES = [
    "Azimio la Kazi (Scheme of Work)",
    "Andalio la Somo (Lesson Plan)",
    "Ratiba ya Vipindi (Timetable)",
    "Matokeo ya Mtihani (Exam Results)",
    "Jaribio/Mtihani (Quiz)",
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

        # Drop any leftover one-product-per-tool rows from before the
        # 2026-08-19 collapse into a single subscription product -
        # FeaturedListing rows pointing at them cascade-delete too.
        removed, _ = Product.objects.filter(
            business=business, name__in=LEGACY_PER_TOOL_PRODUCT_NAMES
        ).delete()
        if removed:
            self.stdout.write(self.style.SUCCESS(
                f"Imeondolewa bidhaa {removed} za zamani (moja-kwa-kila-zana) za '{business.name}'."
            ))

        currency = self._get_tzs_currency()
        spec = TEACHING_SERVICES_PRODUCT
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
                is_subscription=True,
                language_code="sw",
                external_link=spec["external_link"],
            ),
        )
        if not product_created:
            # get_or_create's defaults only apply on creation - an
            # already-existing row needs these refreshed explicitly.
            update_fields = []
            if not product.is_featured:
                product.is_featured = True
                update_fields.append("is_featured")
            if not product.is_subscription:
                product.is_subscription = True
                update_fields.append("is_subscription")
            if product.description != spec["description"]:
                product.description = spec["description"]
                update_fields.append("description")
            if update_fields:
                product.save(update_fields=update_fields)

        if product_created:
            self.stdout.write(self.style.SUCCESS(
                f"Imeundwa bidhaa '{product.name}' ya '{business.name}'."
            ))
        else:
            self.stdout.write(f"Bidhaa '{product.name}' ya '{business.name}' tayari ipo.")

        self._ensure_featured_listings(business, [product])

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
