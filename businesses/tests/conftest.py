# businesses/tests/conftest.py
import pytest
import uuid
from decimal import Decimal
from datetime import timedelta, datetime
from django.utils import timezone
from django.contrib.gis.geos import Point
from businesses.models.business import Business
from businesses.models.product import Product
from businesses.models.service import Service
from businesses.models.branch import Branch
from businesses.models.review import Review
from businesses.models.order import Order
from businesses.models.category import BusinessCategory
from businesses.models.booking import Booking, BookingLog


@pytest.fixture
def business_factory(db, user_factory, unique_institution):
    """Create a Business instance."""
    def create_business(owner=None, **kwargs):
        owner = owner or user_factory()
        return Business.objects.create(owner=owner,
                                        institution=unique_institution,
                                        name=kwargs.get("name", f"Business {uuid.uuid4().hex[:6]}"),
                                        **{k: v for k, v in kwargs.items() if k != "name"})
    return create_business


@pytest.fixture
def product_factory(db, business_factory, default_currency):
    """Create a Product for a Business."""
    def create_product(business=None, **kwargs):
        business = business or business_factory()
        kwargs.setdefault("price", Decimal("50.00"))
        kwargs.setdefault("slug", f"product-{uuid.uuid4().hex[:6]}")
        kwargs.setdefault("quantity_in_stock", 10)
        kwargs.setdefault("is_available", True)
        kwargs.setdefault("is_featured", False)
        kwargs.setdefault("language_code", "sw")
        kwargs.setdefault("tax_inclusive", True)
        kwargs.setdefault("tax_rate", 18)
        # Product.currency is a FK to payments.Currency (not a plain "TZS" string)
        kwargs.setdefault("currency", default_currency)
        kwargs.setdefault("unit", "pcs")
        if isinstance(kwargs.get("currency"), str):
            from payments.models.currency import Currency
            kwargs["currency"] = Currency.objects.get_or_create(code=kwargs["currency"])[0]
        return Product.objects.create(business=business, **kwargs)
    return create_product


@pytest.fixture
def service_factory(db, business_factory):
    def create_service(business=None, **kwargs):
        business = business or business_factory()
        kwargs.setdefault("price", Decimal("100.00"))
        kwargs.setdefault("duration_minutes", 30)  # ✅ Default value to prevent NoneType
        name = kwargs.get("name", f"Service {uuid.uuid4().hex[:6]}")
        return Service.objects.create(
            business=business,
            name=name,
            **{k: v for k, v in kwargs.items() if k not in ["name", "price"]},
            price=kwargs["price"],
        )
    return create_service


@pytest.fixture
def branch_factory(db, business_factory):
    """Create a Branch for a Business."""
    def create_branch(business=None, **kwargs):
        business = business or business_factory()
        kwargs.setdefault("location", Point(39.278, -6.792))
        return Branch.objects.create(business=business, **kwargs)
    return create_branch


@pytest.fixture
def review_factory(db, business_factory, user_factory):
    """Create a Review for a Business."""
    def create_review(business=None, user=None, **kwargs):
        business = business or business_factory()
        user = user or user_factory()
        return Review.objects.create(business=business, user=user, **kwargs)
    return create_review


@pytest.fixture
def setup_review(db, business_factory, product_factory, service_factory, user_factory):
    """Bundle of business/product/service/user plus one review - used by review view tests."""
    business = business_factory()
    product = product_factory(business=business)
    service = service_factory(business=business)
    user = user_factory(role="CLIENT")
    review = Review.objects.create(
        user=user,
        product=product,
        rating=4,
        content="Huduma nzuri sana",
    )
    return {
        "business": business,
        "product": product,
        "service": service,
        "user": user,
        "review": review,
    }


@pytest.fixture
def category_factory(db):
    """Create a Category for a Business."""
    def create_category(**kwargs):
        # Toa 'name' ikiwa ipo ndani ya kwargs, au tengeneza mpya
        name = kwargs.pop("name", f"Category {uuid.uuid4().hex[:6]}")
        # Jenga slug ikiwa haipo
        kwargs.setdefault("slug", name.lower().replace(" ", "-"))
        return BusinessCategory.objects.create(name=name, **kwargs)
    return create_category


@pytest.fixture
def order_factory(db, business_factory, user_factory, product_factory):
    """Create an Order for a Business, optionally overriding created_at."""
    def create_order(business=None, client=None, total_amount=100.00, **kwargs):
        business = business or business_factory()
        client = client or user_factory(role="CLIENT")
        created_at = kwargs.pop("created_at", None)

        order = Order.objects.create(business=business,
                                      client=client,
                                      total_amount=Decimal(total_amount),
                                      **kwargs)

        if business.products.exists():
            product = business.products.first()
            order.items.create(product=product,
                                quantity=1,
                                unit_price=Decimal(total_amount),
                                total_price=Decimal(total_amount))
        if created_at:
            Order.objects.filter(pk=order.pk).update(created_at=created_at)

        return Order.objects.get(pk=order.pk)
    return create_order


@pytest.fixture
def booking_factory(db, service_factory, user_factory):
    from datetime import timedelta
    def create_booking(service=None, client=None, **kwargs):
        if not service:
            service = service_factory(duration_minutes=30)  # ✅ Ensure not None
        if not client:
            client = user_factory()
        future_date = kwargs.pop("scheduled_datetime", timezone.now() + timedelta(days=1))
        return Booking.objects.create(
            service=service,
            client=client,
            scheduled_datetime=future_date,
            status=kwargs.pop("status", "PENDING"),
            payment_status=kwargs.pop("payment_status", "PENDING"),
            **kwargs
        )
    return create_booking


@pytest.fixture
def booking_log_factory(db, booking_factory, user_factory):
    """Create a BookingLog for a Booking"""
    def create_log(booking=None, user=None, **kwargs):
        booking = booking or booking_factory()
        user = user or user_factory()

        kwargs.setdefault("actor_type", "CLIENT")
        kwargs.setdefault("action", "CREATED")
        kwargs.setdefault("ip_address", "127.0.0.1")
        kwargs.setdefault("user_agent", "TestAgent")
        kwargs.setdefault("metadata", {"example": "meta"})

        return BookingLog.objects.create(
            booking=booking,
            user=user,
            **kwargs
        )
    return create_log
