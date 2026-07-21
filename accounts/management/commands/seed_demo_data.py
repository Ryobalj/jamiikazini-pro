# accounts/management/commands/seed_demo_data.py

from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.gis.geos import Point
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from accounts.models import User
from agriculture.models.harvest_contract import HarvestContract, HarvestContractStatus
from billpay.models.bill_payment import BillPayment, BillPaymentStatus
from billpay.models.biller import Biller
from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from businesses.models.featured_listing import FeaturedListing
from businesses.models.order import (
    FulfillmentType, Order, OrderItem, OrderStatus, PaymentMethod, PaymentStatus,
)
from businesses.models.product import Product
from businesses.models.product_image import ProductImage
from businesses.models.service import Service
from construction.models.construction_project import ConstructionProject
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.transfer import Transfer
from jamiiwallet.models.wallet import Wallet
from kiini.models.institution import Institution
from kiini.models.institution_tier import InstitutionTier
from kiini.models.institution_type import InstitutionType
from logistics.choices import TransportTypeChoices
from logistics.models.driver import Driver
from logistics.models.shipment import Shipment, ShipmentStatus
from logistics.models.transport_provider import TransportProvider
from logistics.models.vehicle import Vehicle
from payments.models.currency import Currency
from realestate.models.property_listing import PropertyListing, PropertyListingType, PropertyType
from savings.models.contribution import Contribution
from savings.models.group_membership import GroupMemberRole, GroupMembership
from savings.models.group_wallet import GroupWallet
from savings.models.savings_group import SavingsGroup

DEMO_PASSWORD = "Demo@2026"

DAR_ES_SALAAM = Point(39.2083, -6.7924, srid=4326)
KIGAMBONI = Point(39.2694, -6.8300, srid=4326)

USERS = [
    dict(key="amina", email="amina.hassan@example.com", full_name="Amina Hassan", role="INSTITUTION_ADMIN", phone="255712000001"),
    dict(key="juma", email="juma.mwakalinga@example.com", full_name="Juma Mwakalinga", role="PROVIDER", phone="255712000002"),
    dict(key="fatuma", email="fatuma.ally@example.com", full_name="Fatuma Ally", role="PROVIDER", phone="255712000003"),
    dict(key="baraka", email="baraka.chuma@example.com", full_name="Baraka Chuma", role="TRANSPORTER", phone="255712000004"),
    dict(key="grace", email="grace.mushi@example.com", full_name="Grace Mushi", role="CLIENT", phone="255712000005"),
    dict(key="peter", email="peter.ndosi@example.com", full_name="Peter Ndosi", role="CLIENT", phone="255712000006"),
    dict(key="neema", email="neema.joseph@example.com", full_name="Neema Joseph", role="CLIENT", phone="255712000007"),
    dict(key="halima", email="halima.rashid@example.com", full_name="Halima Rashid", role="CLIENT", phone="255712000008"),
]

WALLET_FUNDING = {
    "amina": Decimal("500000.00"),
    "juma": Decimal("1200000.00"),
    "fatuma": Decimal("900000.00"),
    "baraka": Decimal("150000.00"),
    "grace": Decimal("400000.00"),
    "peter": Decimal("350000.00"),
    "neema": Decimal("250000.00"),
    "halima": Decimal("180000.00"),
}


def _placeholder_image(text, bg_color):
    """Generate a simple colored placeholder JPEG with the product name on it.
    No real product photos exist for demo data, so this gives the homepage/
    storefront something visual to render instead of a blank icon."""
    width, height = 640, 480
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except OSError:
        font = ImageFont.load_default()

    lines = text.split(" ")
    # Wrap into at most 3 lines so long product names still fit the canvas.
    wrapped, current = [], ""
    for word in lines:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) > width - 60 and current:
            wrapped.append(current)
            current = word
        else:
            current = candidate
    if current:
        wrapped.append(current)

    line_height = 52
    total_height = line_height * len(wrapped)
    y = (height - total_height) / 2
    for line in wrapped:
        line_width = draw.textlength(line, font=font)
        draw.text(((width - line_width) / 2, y), line, fill="white", font=font)
        y += line_height

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


class Command(BaseCommand):
    help = "Seed a small set of realistic East African demo data across the whole platform, for presentations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete previously seeded demo data before reseeding.",
        )
        parser.add_argument(
            "--clear-only",
            action="store_true",
            help="Delete previously seeded demo data and exit, without reseeding. "
                 "Use this to permanently remove the demo dataset (e.g. before going fully live).",
        )

    def handle(self, *args, **options):
        if options["clear_only"]:
            with transaction.atomic():
                self._clear()
            self.stdout.write(self.style.SUCCESS("Demo data cleared. Nothing reseeded (--clear-only)."))
            return

        with transaction.atomic():
            if options["clear"]:
                self._clear()

            self.stdout.write("1/10 Seeding reference/lookup data...")
            self._seed_lookups()

            self.stdout.write("2/10 Creating demo users...")
            u = self._seed_users()

            self.stdout.write("3/10 Creating institution...")
            institution = self._seed_institution(u)

            self.stdout.write("4/10 Creating businesses, products & services...")
            biz = self._seed_businesses(u, institution)

            self.stdout.write("5/10 Funding wallets...")
            self._fund_wallets(u)

            self.stdout.write("6/10 Creating orders...")
            self._seed_orders(u, biz)

            self.stdout.write("6b/10 Creating sponsored/featured listings...")
            self._seed_featured_listings(u, biz)

            self.stdout.write("7/10 Creating P2P transfer...")
            self._seed_transfer(u)

            self.stdout.write("8/10 Creating savings group...")
            self._seed_savings_group(u)

            self.stdout.write("9/10 Creating logistics, agriculture, billpay, real estate & construction...")
            self._seed_logistics(u, biz)
            self._seed_agriculture(u, biz)
            self._seed_billpay(u)
            self._seed_realestate(biz)
            self._seed_construction(u)

            self.stdout.write("10/10 Done.")

        self._print_summary()

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------
    def _clear(self):
        # Business/Institution use on_delete=SET_NULL for owner (a real user
        # might legitimately keep owning a business after account deletion
        # elsewhere in the app), so deleting the demo Users alone leaves them
        # orphaned instead of removed. Everything else (products, services,
        # orders, savings groups, transfers, shipments, etc.) does cascade
        # correctly from either the User or the Business FK, so deleting
        # these two by name is enough to erase the whole demo tree.
        business_names = ["Mwakalinga Electronics", "Fatuma Fresh Produce", "Amani Properties"]
        deleted_biz, _ = Business.objects.filter(name__in=business_names).delete()

        deleted_inst, _ = Institution.objects.filter(name="Amani SACCOS").delete()

        emails = [row["email"] for row in USERS]
        deleted_users, _ = User.objects.filter(email__in=emails).delete()

        total = deleted_biz + deleted_inst + deleted_users
        if total:
            self.stdout.write(self.style.WARNING(f"Cleared {total} previously seeded demo records."))

    def _seed_lookups(self):
        for cmd in [
            "seed_currencies",
            "create_institution_choices",
            "seed_business_categories",
            "seed_product_categories",
            "seed_billers",
            "seed_transport_rate_cards",
        ]:
            call_command(cmd, verbosity=0)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    def _seed_users(self):
        users = {}
        for row in USERS:
            user = User.objects.filter(email=row["email"]).first()
            if not user:
                user = User.objects.create_user(
                    email=row["email"],
                    password=DEMO_PASSWORD,
                    full_name=row["full_name"],
                    role=row["role"],
                    phone_number=row["phone"],
                    is_verified=True,
                    is_phone_verified=True,
                )
            users[row["key"]] = user
        return users

    # ------------------------------------------------------------------
    # Institution
    # ------------------------------------------------------------------
    def _seed_institution(self, u):
        tier = InstitutionTier.objects.filter(name="SMALL").first()
        itype = InstitutionType.objects.filter(name="COOPERATIVE").first()
        institution, _ = Institution.objects.get_or_create(
            name="Amani SACCOS",
            defaults=dict(
                owner=u["amina"],
                tier=tier,
                institution_type=itype,
                email="info@amanisaccos.example.com",
                phone="255712000001",
                address="Kariakoo, Dar es Salaam",
                location=DAR_ES_SALAAM,
            ),
        )
        if not u["amina"].institution_id:
            u["amina"].institution = institution
            u["amina"].save(update_fields=["institution"])
        return institution

    # ------------------------------------------------------------------
    # Businesses, products, services
    # ------------------------------------------------------------------
    def _seed_businesses(self, u, institution):
        tech_cat = BusinessCategory.objects.filter(slug="technology").first()
        agric_cat = BusinessCategory.objects.filter(slug="agriculture").first()
        tzs = Currency.objects.filter(code="TZS").first()

        electronics, _ = Business.objects.get_or_create(
            name="Mwakalinga Electronics",
            defaults=dict(
                owner=u["juma"],
                category=tech_cat,
                description="Phones, TVs, and electrical equipment - Kariakoo, Dar es Salaam.",
                phone="255712000002",
                address="Kariakoo, Dar es Salaam",
                location=DAR_ES_SALAAM,
                is_verified=True,
            ),
        )
        produce, _ = Business.objects.get_or_create(
            name="Fatuma Fresh Produce",
            defaults=dict(
                owner=u["fatuma"],
                category=agric_cat,
                description="Fresh farm produce straight from the field - maize, rice, vegetables.",
                phone="255712000003",
                address="Morogoro Road, Dar es Salaam",
                location=DAR_ES_SALAAM,
                deals_in_agriculture=True,
                is_verified=True,
            ),
        )
        properties, _ = Business.objects.get_or_create(
            name="Amani Properties",
            defaults=dict(
                owner=u["amina"],
                institution=institution,
                description="Renting and selling houses and land - Dar es Salaam.",
                is_verified=True,
            ),
        )

        def _product(business, name, price, unit="pcs", qty=Decimal("25"), image_color=None):
            obj, _ = Product.objects.get_or_create(
                business=business,
                name=name,
                defaults=dict(price=price, currency=tzs, quantity_in_stock=qty, unit=unit),
            )
            if not obj.image and image_color:
                obj.image.save(
                    f"{slugify(name)}.jpg",
                    ContentFile(_placeholder_image(name, image_color)),
                    save=True,
                )
            return obj

        p_phone = _product(electronics, "Tecno Spark Mobile Phone", Decimal("320000.00"), qty=Decimal("15"), image_color="#2563eb")
        p_tv = _product(electronics, '43" Smart TV', Decimal("650000.00"), qty=Decimal("8"), image_color="#4f46e5")
        p_maize = _product(produce, "Maize (Sack)", Decimal("75000.00"), unit="gunia", qty=Decimal("120"), image_color="#92400e")
        p_rice = _product(produce, "Rice (25kg)", Decimal("68000.00"), unit="pack", qty=Decimal("60"), image_color="#16a34a")

        # A couple of gallery photos on the phone, to demonstrate the
        # ProductImage gallery (extra angles beyond the main product.image).
        for i, (caption, color) in enumerate([
            ("Side view", "#1d4ed8"),
            ("Box contents", "#1e3a8a"),
        ]):
            if not ProductImage.objects.filter(product=p_phone, caption=caption).exists():
                gallery_image = ProductImage(product=p_phone, caption=caption, order=i)
                gallery_image.image.save(
                    f"{p_phone.slug}-{slugify(caption)}.jpg",
                    ContentFile(_placeholder_image(caption, color)),
                    save=False,
                )
                gallery_image.save()

        Service.objects.get_or_create(
            business=electronics,
            name="Phone & TV Repair",
            defaults=dict(price=Decimal("15000.00"), billing_type="ONE_TIME"),
        )

        return {
            "electronics": electronics,
            "produce": produce,
            "properties": properties,
            "p_phone": p_phone,
            "p_tv": p_tv,
            "p_maize": p_maize,
            "p_rice": p_rice,
        }

    # ------------------------------------------------------------------
    # Wallets
    # ------------------------------------------------------------------
    def _fund_wallets(self, u):
        for key, amount in WALLET_FUNDING.items():
            user = u[key]
            wallet = Wallet.objects.get(user=user)
            if wallet.balance > 0:
                continue
            Transaction.objects.create(
                wallet=wallet,
                currency=wallet.currency,
                initiated_by=user,
                transaction_type=Transaction.TransactionType.TOP_UP,
                status=Transaction.TransactionStatus.COMPLETED,
                amount=amount,
                metadata={"source": "demo_seed"},
            )
            wallet.balance = amount
            wallet.save(update_fields=["balance"])

    def _debit_for_order(self, user, order):
        wallet = Wallet.objects.get(user=user)
        Transaction.objects.create(
            wallet=wallet,
            currency=wallet.currency,
            initiated_by=user,
            transaction_type=Transaction.TransactionType.PAYMENT,
            status=Transaction.TransactionStatus.COMPLETED,
            amount=order.total_amount,
            metadata={"order_id": str(order.id)},
        )
        wallet.balance -= order.total_amount
        wallet.save(update_fields=["balance"])

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    def _seed_orders(self, u, biz):
        if not Order.objects.filter(client=u["grace"], business=biz["electronics"]).exists():
            order1 = Order.objects.create(
                client=u["grace"],
                business=biz["electronics"],
                status=OrderStatus.COMPLETED,
                payment_status=PaymentStatus.PAID,
                payment_method=PaymentMethod.WALLET,
                fulfillment_type=FulfillmentType.DELIVERY,
            )
            OrderItem.objects.create(order=order1, product=biz["p_phone"], unit_price=biz["p_phone"].price, quantity=1)
            order1.refresh_from_db()
            self._debit_for_order(u["grace"], order1)

        if not Order.objects.filter(client=u["peter"], business=biz["produce"]).exists():
            order2 = Order.objects.create(
                client=u["peter"],
                business=biz["produce"],
                status=OrderStatus.PROCESSING,
                payment_status=PaymentStatus.PAID,
                payment_method=PaymentMethod.WALLET,
                fulfillment_type=FulfillmentType.PICKUP,
            )
            OrderItem.objects.create(order=order2, product=biz["p_maize"], unit_price=biz["p_maize"].price, quantity=2)
            order2.refresh_from_db()
            self._debit_for_order(u["peter"], order2)

    # ------------------------------------------------------------------
    # Featured / sponsored listings (homepage "Sponsored Listings" section)
    # ------------------------------------------------------------------
    def _seed_featured_listings(self, u, biz):
        today = date.today()
        listings = [
            (biz["electronics"], biz["p_phone"], u["juma"]),
            (biz["electronics"], biz["p_tv"], u["juma"]),
            (biz["produce"], biz["p_maize"], u["fatuma"]),
        ]
        for business, product, owner in listings:
            if FeaturedListing.objects.filter(business=business, product=product).exists():
                continue
            FeaturedListing.objects.create(
                business=business,
                product=product,
                start_date=today - timedelta(days=1),
                end_date=today + timedelta(days=30),
                amount=FeaturedListing.calculate_amount(31),
                is_active=True,
                created_by=owner,
            )

    # ------------------------------------------------------------------
    # P2P transfer
    # ------------------------------------------------------------------
    def _seed_transfer(self, u):
        if Transfer.objects.filter(sender=u["grace"], recipient=u["halima"]).exists():
            return

        sender_wallet = Wallet.objects.get(user=u["grace"])
        recipient_wallet = Wallet.objects.get(user=u["halima"])
        amount = Decimal("50000.00")

        transfer = Transfer.objects.create(
            sender=u["grace"], recipient=u["halima"], amount=amount, note="For school fees",
        )
        sender_txn = Transaction.objects.create(
            wallet=sender_wallet,
            currency=sender_wallet.currency,
            initiated_by=u["grace"],
            counterparty=u["halima"],
            transaction_type=Transaction.TransactionType.TRANSFER,
            status=Transaction.TransactionStatus.COMPLETED,
            amount=amount,
        )
        recipient_txn = Transaction.objects.create(
            wallet=recipient_wallet,
            currency=recipient_wallet.currency,
            initiated_by=u["grace"],
            counterparty=u["grace"],
            transaction_type=Transaction.TransactionType.TRANSFER,
            status=Transaction.TransactionStatus.COMPLETED,
            amount=amount,
        )
        transfer.mark_completed(sender_txn, recipient_txn)

        sender_wallet.balance -= amount
        sender_wallet.save(update_fields=["balance"])
        recipient_wallet.balance += amount
        recipient_wallet.save(update_fields=["balance"])

    # ------------------------------------------------------------------
    # Savings group
    # ------------------------------------------------------------------
    def _seed_savings_group(self, u):
        tzs = Currency.objects.filter(code="TZS").first()
        group, _ = SavingsGroup.objects.get_or_create(
            name="Umoja Savings Group",
            defaults=dict(created_by=u["neema"], currency=tzs),
        )
        group_wallet, _ = GroupWallet.objects.get_or_create(group=group, defaults=dict(currency=tzs))

        memberships = [
            (u["neema"], GroupMemberRole.ADMIN, Decimal("20000.00")),
            (u["halima"], GroupMemberRole.MEMBER, Decimal("20000.00")),
            (u["grace"], GroupMemberRole.MEMBER, Decimal("20000.00")),
        ]
        for member, role, contribution_amount in memberships:
            GroupMembership.objects.get_or_create(
                group=group, user=member, defaults=dict(role=role, contribution_amount=contribution_amount),
            )

        if not Contribution.objects.filter(group=group).exists():
            for member, _role, amount in memberships:
                Contribution.objects.create(group=group, member=member, amount=amount)
                group_wallet.balance += amount
            group_wallet.save(update_fields=["balance"])

    # ------------------------------------------------------------------
    # Logistics
    # ------------------------------------------------------------------
    def _seed_logistics(self, u, biz):
        provider, _ = TransportProvider.objects.get_or_create(
            user=u["baraka"],
            defaults=dict(provider_type=TransportProvider.ProviderType.INDIVIDUAL, location=DAR_ES_SALAAM),
        )
        driver, _ = Driver.objects.get_or_create(
            license_number="DL-TZ-2026-00042",
            defaults=dict(transport_provider=provider, full_name="Baraka Chuma", phone_number="255712000004", is_verified=True),
        )
        vehicle, _ = Vehicle.objects.get_or_create(
            registration_number="T123 ABC",
            defaults=dict(
                provider=provider,
                vehicle_type=TransportTypeChoices.SUZUKI_CARRY,
                model_name="Suzuki Carry",
                capacity_kg=1000,
            ),
        )
        vehicle.drivers.add(driver)
        if not vehicle.active_driver_id:
            vehicle.active_driver = driver
            vehicle.save(update_fields=["active_driver"])

        if not Shipment.objects.filter(sender=u["juma"], receiver=u["grace"]).exists():
            shipment = Shipment.objects.create(
                product=biz["p_tv"],
                sender=u["juma"],
                receiver=u["grace"],
                preferred_transport_modes=["TRUCK"],
                status=ShipmentStatus.IN_TRANSIT,
                transport_fee=Decimal("15000.00"),
                total_cost=Decimal("665000.00"),
            )
            shipment.transport_providers.add(provider)

    # ------------------------------------------------------------------
    # Agriculture
    # ------------------------------------------------------------------
    def _seed_agriculture(self, u, biz):
        if HarvestContract.objects.filter(buyer=u["peter"], seller=biz["produce"]).exists():
            return
        today = date.today()
        HarvestContract.objects.create(
            buyer=u["peter"],
            seller=biz["produce"],
            crop_description="Seasonal Maize",
            estimated_weight_kg=Decimal("2000.000"),
            agreed_price_per_kg=Decimal("900.00"),
            delivery_window_start=today + timedelta(days=30),
            delivery_window_end=today + timedelta(days=60),
            status=HarvestContractStatus.PENDING,
        )

    # ------------------------------------------------------------------
    # Billpay
    # ------------------------------------------------------------------
    def _seed_billpay(self, u):
        tzs = Currency.objects.filter(code="TZS").first()
        biller = Biller.objects.filter(config_key="TZ_LUKU").first()
        if not biller or BillPayment.objects.filter(user=u["grace"], biller=biller).exists():
            return

        wallet = Wallet.objects.get(user=u["grace"])
        amount = Decimal("20000.00")
        txn = Transaction.objects.create(
            wallet=wallet,
            currency=tzs,
            initiated_by=u["grace"],
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            status=Transaction.TransactionStatus.COMPLETED,
            amount=amount,
        )
        BillPayment.objects.create(
            user=u["grace"],
            biller=biller,
            account_number="01234567890",
            amount=amount,
            currency=tzs,
            status=BillPaymentStatus.COMPLETED,
            wallet_transaction=txn,
        )
        wallet.balance -= amount
        wallet.save(update_fields=["balance"])

    # ------------------------------------------------------------------
    # Real estate
    # ------------------------------------------------------------------
    def _seed_realestate(self, biz):
        tzs = Currency.objects.filter(code="TZS").first()
        PropertyListing.objects.get_or_create(
            owner=biz["properties"],
            title_deed_number="TD-DSM-000123",
            defaults=dict(
                listing_type=PropertyListingType.RENT,
                property_type=PropertyType.APARTMENT,
                location=DAR_ES_SALAAM,
                address_text="Masaki, Dar es Salaam",
                price=Decimal("900000.00"),
                deposit_amount=Decimal("900000.00"),
                currency=tzs,
                bedrooms=3,
                bathrooms=2,
                size_sqm=Decimal("120.00"),
                description="Modern 3-bedroom apartment near the Masaki beachfront.",
            ),
        )

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _seed_construction(self, u):
        if ConstructionProject.objects.filter(client=u["peter"]).exists():
            return
        ConstructionProject.objects.create(
            client=u["peter"],
            scope_description="Construction of a 3-bedroom house with a concrete foundation - Kigamboni, Dar es Salaam.",
            location=KIGAMBONI,
            budget_ceiling=Decimal("45000000.00"),
        )

    # ------------------------------------------------------------------
    def _print_summary(self):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Demo data ready. All demo users share password: {DEMO_PASSWORD}"))
        for row in USERS:
            self.stdout.write(f"  {row['email']:<28} {row['role']}")
