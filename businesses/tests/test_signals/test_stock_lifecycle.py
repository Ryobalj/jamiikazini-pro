# businesses/tests/test_signals/test_stock_lifecycle.py

import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient

from businesses.models.order import Order, OrderStatus


@pytest.mark.django_db
def test_order_item_creation_decrements_stock(business_factory, product_factory, user_factory):
    business = business_factory()
    product = product_factory(business=business, quantity_in_stock=10)
    client = user_factory(role="CLIENT")

    order = Order.objects.create(business=business, client=client, total_amount=Decimal("0"))
    order.items.create(product=product, quantity=3, unit_price=product.price, total_price=product.price * 3)

    product.refresh_from_db()
    assert product.quantity_in_stock == 7


@pytest.mark.django_db
def test_cancelling_order_restores_stock(business_factory, product_factory, user_factory):
    business = business_factory()
    product = product_factory(business=business, quantity_in_stock=10)
    client = user_factory(role="CLIENT")

    order = Order.objects.create(business=business, client=client, total_amount=Decimal("0"))
    order.items.create(product=product, quantity=4, unit_price=product.price, total_price=product.price * 4)
    product.refresh_from_db()
    assert product.quantity_in_stock == 6

    order.status = OrderStatus.CANCELLED
    order.save()

    product.refresh_from_db()
    assert product.quantity_in_stock == 10


@pytest.mark.django_db
def test_cancelling_twice_does_not_double_restore(business_factory, product_factory, user_factory):
    business = business_factory()
    product = product_factory(business=business, quantity_in_stock=10)
    client = user_factory(role="CLIENT")

    order = Order.objects.create(business=business, client=client, total_amount=Decimal("0"))
    order.items.create(product=product, quantity=2, unit_price=product.price, total_price=product.price * 2)

    order.status = OrderStatus.CANCELLED
    order.save()
    order.save()  # re-save while already cancelled - should be a no-op for stock

    product.refresh_from_db()
    assert product.quantity_in_stock == 10  # not 12


@pytest.mark.django_db
def test_restock_endpoint_increments_stock(business_factory, product_factory):
    business = business_factory()
    product = product_factory(business=business, quantity_in_stock=5, language_code="en")

    client = APIClient()
    client.force_authenticate(user=business.owner)

    url = reverse("businesses:business-products-restock", kwargs={"business_pk": business.id, "slug": product.slug})
    resp = client.post(url, {"quantity": 20}, format="json")

    assert resp.status_code == 200, resp.content
    product.refresh_from_db()
    assert product.quantity_in_stock == 25


@pytest.mark.django_db
def test_restock_rejects_non_owner(business_factory, product_factory, user_factory):
    business = business_factory()
    product = product_factory(business=business, quantity_in_stock=5, language_code="en")
    stranger = user_factory()

    client = APIClient()
    client.force_authenticate(user=stranger)

    url = reverse("businesses:business-products-restock", kwargs={"business_pk": business.id, "slug": product.slug})
    resp = client.post(url, {"quantity": 10}, format="json")

    assert resp.status_code == 403
    product.refresh_from_db()
    assert product.quantity_in_stock == 5
