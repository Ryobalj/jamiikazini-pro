import pytest
from payments.models.currency import Currency
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from businesses.models.product import Product
from businesses.models.business import Business
from businesses.serializers.product_serializer import (
    ProductSerializer,
    ProductDetailSerializer,
    ProductMinimalSerializer,
    ProductListSerializer,
)
from accounts.models import User
from kiini.models.institution import Institution


@pytest.mark.django_db
class TestProductSerializers:

    @pytest.fixture
    def sample_product(self):
        institution = Institution.objects.create(name="Test Institution")
        owner = User.objects.create_user(email="owner@example.com", password="testpass", institution=institution)
        business = Business.objects.create(
            institution=institution,
            owner=owner,
            name="Test Business"
        )
        return Product.objects.create(
            business=business,
            name="Sabuni Asili",
            slug="sabuni-asili",
            type="physical",
            price=Decimal("10000.00"),
            discount_price=Decimal("9000.00"),
            currency=Currency.objects.get_or_create(code="TZS")[0],
            quantity_in_stock=20,
            unit="pcs",
            is_available=True,
            is_featured=False,
            tax_inclusive=True,
            tax_rate=Decimal("18.00"),
            language_code="sw"
        )

    def test_product_serializer_valid_data(self, sample_product):
        serializer = ProductSerializer(instance=sample_product)
        data = serializer.data
        assert data["name"] == "Sabuni Asili"
        assert data["price"] == "10000.00"
        assert data["discount_price"] == "9000.00"
        assert "final_price" in data
        assert data["final_price"] == sample_product.final_price()
        assert data["has_stock"] is True
        assert data["is_digital"] is False
        assert data["is_service"] is False

    def test_product_serializer_discount_validation(self, sample_product):
        product_data = {
            "business": str(sample_product.business.id),
            "name": "Paka Cream",
            "slug": "paka-cream",
            "type": "physical",
            "price": "5000.00",
            "discount_price": "7000.00",  # invalid
            # currency ni nullable - tunaacha ili validation ya discount ifike
            "quantity_in_stock": 10,
            "unit": "pcs",
            "is_available": True,
            "is_featured": False,
            "tax_inclusive": True,
            "tax_rate": "18.00",
            "language_code": "sw"
        }
        serializer = ProductSerializer(data=product_data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_product_detail_serializer_output(self, sample_product):
        serializer = ProductDetailSerializer(instance=sample_product)
        data = serializer.data
        assert data["name"] == "Sabuni Asili"
        assert data["final_price"] == sample_product.final_price()
        assert data["has_stock"] is True
        assert data["is_digital"] is False
        assert data["is_service"] is False

    def test_product_minimal_serializer_output(self, sample_product):
        serializer = ProductMinimalSerializer(instance=sample_product)
        data = serializer.data
        assert "id" in data
        assert data["final_price"] == sample_product.final_price()
        assert "name" in data
        assert "image" in data

    def test_product_list_serializer_output(self, sample_product):
        serializer = ProductListSerializer(instance=sample_product)
        data = serializer.data
        assert "final_price" in data
        assert data["final_price"] == sample_product.final_price()
        assert data["is_available"] is True