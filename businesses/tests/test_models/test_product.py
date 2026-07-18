# businesses/tests/test_models/test_product.py

import pytest
from decimal import Decimal
from businesses.models.product import Product, ProductType
from businesses.models.business import Business
from kiini.models.institution import Institution
from accounts.models import User

pytestmark = pytest.mark.django_db

class TestProductModel:
    def setup_method(self):
        self.institution = Institution.objects.create(name="Tech Institute", domain="tech")
        self.owner = User.objects.create_user(email="owner@tech.com", full_name="Tech Owner", password="pass123", institution=self.institution)
        self.business = Business.objects.create(name="Tech Store", slug="tech-store", owner=self.owner, institution=self.institution)

    def test_str_representation(self):
        product = Product.objects.create(
            business=self.business,
            name="Wireless Mouse",
            slug="wireless-mouse",
            description="Bluetooth-enabled",
            price=25000,
        )
        assert str(product) == "Wireless Mouse - Tech Store"

    def test_final_price_with_discount(self):
        product = Product.objects.create(
            business=self.business,
            name="Monitor",
            slug="monitor",
            price=300000,
            discount_price=250000,
        )
        assert product.final_price() == Decimal("250000")

    def test_final_price_without_discount(self):
        product = Product.objects.create(
            business=self.business,
            name="Keyboard",
            slug="keyboard",
            price=80000,
        )
        assert product.final_price() == Decimal("80000")

    def test_has_stock(self):
        product = Product.objects.create(
            business=self.business,
            name="Webcam",
            slug="webcam",
            price=90000,
            quantity_in_stock=5,
        )
        assert product.has_stock() is True

    def test_has_no_stock(self):
        product = Product.objects.create(
            business=self.business,
            name="Microphone",
            slug="microphone",
            price=70000,
            quantity_in_stock=0,
        )
        assert product.has_stock() is False

    def test_is_digital(self):
        product = Product.objects.create(
            business=self.business,
            name="E-book",
            slug="ebook",
            price=15000,
            type=ProductType.DIGITAL,
        )
        assert product.is_digital() is True
        assert product.is_service() is False

    def test_is_service(self):
        product = Product.objects.create(
            business=self.business,
            name="Installation Service",
            slug="install-service",
            price=50000,
            type=ProductType.SERVICE,
        )
        assert product.is_service() is True
        assert product.is_digital() is False

    def test_quantity_in_stock_supports_fractional_kg_amounts(self):
        product = Product.objects.create(
            business=self.business,
            name="Sukari",
            slug="sukari",
            price=2000,
            unit="kg",
            quantity_in_stock=Decimal("2.5"),
        )
        product.refresh_from_db()
        assert product.quantity_in_stock == Decimal("2.500")
        assert product.has_stock() is True