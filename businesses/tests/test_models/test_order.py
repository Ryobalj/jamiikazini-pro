# businesses/tests/test_models/test_order.py

import pytest
from decimal import Decimal
from businesses.models.order import Order, OrderItem

pytestmark = pytest.mark.django_db


def test_order_calculate_total(business_factory, admin_user, product_factory, service_factory):
    """Hakikisha total_amount ya Order inakokotwa ipasavyo."""
    business = business_factory()
    order = Order.objects.create(business=business, client=admin_user, total_amount=Decimal("0.00"))

    p1 = product_factory(business=business, price=Decimal("10.00"))
    s1 = service_factory(business=business, price=Decimal("15.00"))

    OrderItem.objects.create(order=order, product=p1, quantity=2, unit_price=Decimal("10.00"))
    OrderItem.objects.create(order=order, service=s1, quantity=1, unit_price=Decimal("15.00"))
    order.save()

    assert order.total_amount == Decimal("35.00")  # 2x10 + 1x15


def test_order_item_total_price(business_factory, admin_user, product_factory):
    """Hakikisha total_price inakokotwa wakati wa save."""
    business = business_factory()
    p1 = product_factory(business=business, price=Decimal("5.00"))
    order = Order.objects.create(business=business, client=admin_user, total_amount=Decimal("0.00"))

    item = OrderItem.objects.create(order=order, product=p1, quantity=3, unit_price=Decimal("5.00"))
    assert item.total_price == Decimal("15.00")


def test_order_item_string(product_factory, business_factory, admin_user):
    """Hakikisha __str__ inafanya kazi ipasavyo."""
    business = business_factory()
    p1 = product_factory(business=business, price=Decimal("5.00"))
    order = Order.objects.create(business=business, client=admin_user, total_amount=Decimal("0.00"))

    item = OrderItem.objects.create(order=order, product=p1, quantity=2, unit_price=Decimal("5.00"))
    assert str(item) == f"2 x {p1.name}"


def test_order_string(business_factory, admin_user):
    """Hakikisha __str__ ya Order inafanya kazi ipasavyo."""
    business = business_factory()
    order = Order.objects.create(business=business, client=admin_user, total_amount=Decimal("100.00"))

    assert str(order).startswith(f"Order {order.id} by {admin_user.email}")


def test_check_constraint_for_order_item(business_factory, admin_user):
    """Hakikisha CheckConstraint inafanya kazi: Product au Service lazima iwepo."""
    business = business_factory()
    order = Order.objects.create(business=business, client=admin_user, total_amount=Decimal("0.00"))

    with pytest.raises(Exception):
        # Hapa hatujaspecify product wala service, constraint lazima ivunjike
        OrderItem.objects.create(order=order, quantity=1, unit_price=Decimal("5.00"))