# conftest.py (ROOT Level)

import os
import pytest
import uuid
import decimal
from decimal import Decimal
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from accounts.models import User
from rest_framework.test import APIClient

from kiini.models.institution import Institution
from kiini.models.institution_type import InstitutionType
from kiini.models.institution_tier import InstitutionTier
from jamiiwallet.models.wallet import Wallet
from payments.models.currency import Currency
from payments.models.invoice import Invoice, InvoiceStatus
from payments.models.paymentmethod import PaymentMethod
from payments.models.payment_report import PaymentReport
from payments.models.payment_failure import PaymentFailure
from payments.models.audit_log import AuditLog
from jamiiwallet.models.transaction import Transaction
from django.contrib.auth import get_user_model
import django.db.models.signals as signals
from django.dispatch import receiver

User = get_user_model()

# Disable wallet auto-creation signal during tests
try:
    signals.post_save.disconnect(
        receiver=Wallet.create_wallet_for_user,
        sender=User
    )
except Exception:
    # In case signal is already disconnected
    pass


os.environ["TESTING"] = "True"


# =======================
#  Global Fixtures
# =======================

@pytest.fixture
def api_client():
    """Provide DRF API Client."""
    return APIClient()


@pytest.fixture(autouse=True)
def clear_ratelimit_cache():
    """Clear cache before every test."""
    cache.clear()

@pytest.fixture
def default_currency(db):
    """Ensure default currency exists."""
    currency, _ = Currency.objects.get_or_create(code="TZS")
    return currency

@pytest.fixture
def user_factory(db, default_currency):
    """Creates a user with wallet and default currency, avoids duplicates."""
    def create_user(**kwargs):
        # Unique email kwa kila user
        email = kwargs.get("email") or f"user_{uuid.uuid4().hex[:8]}@example.com"
        role = kwargs.get("role", "CLIENT")
        full_name = kwargs.get("full_name", "Test User")
        password = kwargs.get("password", "pass123")

        # Determine if user should be superuser/staff
        is_staff = False
        is_superuser = False
        if role == "ADMIN":
            is_staff = True
            is_superuser = True

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=role,
            is_active=True,
            is_staff=is_staff,
            is_superuser=is_superuser,
            **{k: v for k, v in kwargs.items() if k not in ["email", "password", "role", "full_name"]}
        )

        # Only create wallet if it doesn't exist
        if not Wallet.objects.filter(user=user).exists():
            Wallet.objects.create(user=user, currency=default_currency)

        return user

    return create_user


@pytest.fixture
def unique_institution(db):
    """Creates an Institution with a unique name and domain."""
    unique_name = f"Institution_{uuid.uuid4().hex[:6]}"
    return Institution.objects.create(
        name=unique_name,
        domain=f"{unique_name.lower()}.local"
    )


@pytest.fixture
def unique_user(db, unique_institution, user_factory):
    """Creates a unique user attached to the unique institution."""
    return user_factory(institution=unique_institution)


@pytest.fixture
def admin_user(user_factory):
    """Creates an Admin user."""
    return user_factory(email="admin@example.com", role="INSTITUTION_ADMIN", full_name="Admin User")


@pytest.fixture
def client_user(user_factory):
    """Creates a Client user."""
    return user_factory(email="clientuser@example.com", role="CLIENT", full_name="Client User")


@pytest.fixture
def user(user_factory):
    """Creates a generic user."""
    return user_factory(email="user@example.com", role="INSTITUTION_ADMIN", full_name="Normal User")


@pytest.fixture
def superuser_factory(db):
    def create_superuser(**kwargs):
        email = kwargs.get("email") or f"admin_{uuid.uuid4().hex[:6]}@example.com"
        return User.objects.create_user(
            email=email,
            password=kwargs.get("password", "adminpass123"),
            full_name=kwargs.get("full_name", "Admin Superuser"),
            role=kwargs.get("role", "ADMIN"),  # tumia 'ADMIN' badala ya 'SUPERUSER'
            is_superuser=True,                 # muhimu kwa Django permissions
            is_staff=True,                     # ili apate access ya admin panel pia
            **{k: v for k, v in kwargs.items() if k not in ["email", "password", "role", "full_name"]}
        )
    return create_superuser


# =======================
#  Institution Factories
# =======================

@pytest.fixture
def institution_factory(db, user_factory):
    """Create an Institution for a given owner."""
    def create_institution(owner=None, **kwargs):
        owner = owner or user_factory()
        tier = kwargs.pop("tier", InstitutionTier.objects.get_or_create(name="Small")[0])
        inst_type = kwargs.pop("institution_type", InstitutionType.objects.get_or_create(name="PRIVATE_COMPANY")[0])
        name = kwargs.pop("name", f"Institution {uuid.uuid4().hex[:6]}")
        domain = kwargs.pop("domain", f"{name.lower().replace(' ', '')}.com")

        return Institution.objects.create(
            name=name,
            domain=domain,
            owner=owner,
            tier=tier,
            institution_type=inst_type,
            **kwargs
        )
    return create_institution


@pytest.fixture
def tier_factory(db):
    def create_tier(name="Small", **kwargs):
        return InstitutionTier.objects.create(name=name, **kwargs)
    return create_tier


@pytest.fixture
def institution_type_factory(db):
    def create_type(name="PRIVATE_COMPANY", **kwargs):
        return InstitutionType.objects.create(name=name, **kwargs)
    return create_type


# =======================
#  Wallet & Transaction
# =======================

@pytest.fixture
def wallet_factory(db):
    def create_wallet(user, **kwargs):
        defaults = {
            "balance": Decimal("0.00"),
            "is_active": True,
        }
        defaults.update(kwargs)
        wallet, created = Wallet.objects.get_or_create(user=user, defaults=defaults)

        if not created:
            # Force update for existing wallet
            for key, value in defaults.items():
                setattr(wallet, key, value)
            wallet.save()

        return wallet
    return create_wallet


@pytest.fixture
def wallet_with_failed_transaction(db, user_factory, wallet_factory):
    user = user_factory()
    wallet = wallet_factory(user=user, balance=Decimal("0.00"))
    txn = Transaction.objects.create(
        wallet=wallet,
        transaction_type=Transaction.TransactionType.TOP_UP,
        status=Transaction.TransactionStatus.FAILED,
        reference=f"TXN_FAILED_{uuid.uuid4().hex[:8]}",
        amount=Decimal("10.00"),
    )
    yield txn
    # Cleanup
    txn.delete()
    wallet.delete()
    user.delete()


# =======================
#  Payments Factories
# =======================

@pytest.fixture
def currency_factory(db):
    def create_currency(**kwargs):
        defaults = {
            "code": "USD",
            "name": "US Dollar",
            "exchange_rate_to_tzs": Decimal("2500.00")
        }
        defaults.update(kwargs)
        return Currency.objects.create(**defaults)
    return create_currency


@pytest.fixture
def invoice_factory(user_factory):
    def create_invoice(user=None, **kwargs):
        user = user or user_factory()
        amount = kwargs.get("amount", Decimal("100.00"))
        tax = kwargs.get("tax", Decimal("10.00"))
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if not isinstance(tax, Decimal):
            tax = Decimal(str(tax))

        return Invoice.objects.create(
            invoice_number=kwargs.get(
                "invoice_number",
                f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            ),
            user=user,
            amount=amount,
            tax=tax,
            status=kwargs.get("status", InvoiceStatus.PENDING),
            due_date=kwargs.get("due_date", timezone.now().date() + timedelta(days=7)),
            description=kwargs.get("description", "Test invoice"),
            created_by=kwargs.get("created_by", user),
            last_modified_by=kwargs.get("last_modified_by", user),
        )
    return create_invoice

@pytest.fixture
def payment_method_factory(db, user_factory):
    def create_payment_method(owner=None, **kwargs):
        owner = owner or user_factory()
        defaults = {
            "owner": owner,
            "method_type": "WALLET",
            "details": {"dummy": "data"},
            "is_default": False,
        }
        defaults.update(kwargs)
        return PaymentMethod.objects.create(**defaults)
    return create_payment_method


@pytest.fixture
def payment_report_factory():
    def create_payment_report(user=None, **kwargs):
        from payments.models.payment_report import PaymentReport
        from django.utils import timezone
        from accounts.models import User
        from decimal import Decimal

        user = user or User.objects.first()
        defaults = {
            "user": user,
            "transaction_count": 1,
            "total_amount": Decimal("100.00"),
            "report_date": kwargs.get("report_date", timezone.now().date()),
        }
        defaults.update(kwargs)
        return PaymentReport.objects.create(**defaults)
    return create_payment_report


@pytest.fixture
def payment_failure_factory(user_factory):
    def create_payment_failure(user=None, **kwargs):
        from decimal import Decimal
        import uuid
        from payments.models.payment_failure import PaymentFailure

        user = user or user_factory()
        defaults = {
            "user": user,
            "amount": kwargs.get("amount", Decimal("100.00")),
            "currency": kwargs.get("currency", None),
            "reference": kwargs.get("reference", f"TXN_{uuid.uuid4().hex[:8]}"),
            "reason": kwargs.get("reason", "Test failure"),
            "retries": kwargs.get("retries", 0),
        }
        return PaymentFailure.objects.create(**defaults)
    return create_payment_failure

@pytest.fixture
def audit_log_factory(db, user_factory):
    def create_audit_log(user=None, target_obj=None, **kwargs):
        user = user or user_factory()

        content_type = None
        object_id = None
        if target_obj:
            content_type = ContentType.objects.get_for_model(target_obj)
            object_id = getattr(target_obj, "pk", None)

        defaults = {
            "user": user,
            "action": "OTHER",
            "content_type": content_type,
            "object_id": object_id,
            "description": "Test audit log entry",
            "metadata": {"test": "data"},
            "ip_address": "127.0.0.1",
        }
        defaults.update(kwargs)
        return AuditLog.objects.create(**defaults)
    return create_audit_log