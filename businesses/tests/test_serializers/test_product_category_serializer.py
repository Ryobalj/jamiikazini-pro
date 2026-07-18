# businesses/tests/test_serializers/test_product_category_serializer.py

import pytest
from businesses.models.product_category import ProductCategory
from businesses.serializers.product_category_serializer import ProductCategorySerializer

pytestmark = pytest.mark.django_db


def test_valid_category_serialization():
    category = ProductCategory.objects.create(
        name="Vyakula",
        slug="vyakula",
        description="Vyakula vya kila siku"
    )
    serializer = ProductCategorySerializer(category)
    data = serializer.data
    assert data["name"] == "Vyakula"
    assert data["slug"] == "vyakula"
    assert data["description"] == "Vyakula vya kila siku"


def test_category_serializer_with_missing_name():
    data = {
        "slug": "vinywaji",
        "description": "Soda na maji"
    }
    serializer = ProductCategorySerializer(data=data)
    assert not serializer.is_valid()
    assert "name" in serializer.errors


def test_category_serializer_with_valid_data():
    data = {
        "name": "Nguo",
        "slug": "nguo",
        "description": "Mavazi mbalimbali"
    }
    serializer = ProductCategorySerializer(data=data)
    assert serializer.is_valid()
    instance = serializer.save()
    assert instance.name == "Nguo"
    assert instance.slug == "nguo"


def test_category_serializer_rejects_duplicate_slug():
    ProductCategory.objects.create(name="Vyakula", slug="vyakula")
    serializer = ProductCategorySerializer(data={"name": "Vyakula 2", "slug": "vyakula"})
    assert not serializer.is_valid()
    assert "slug" in serializer.errors


def test_category_serializer_includes_parent_name():
    parent = ProductCategory.objects.create(name="Vyakula", slug="vyakula")
    child = ProductCategory.objects.create(name="Nafaka", slug="nafaka", parent=parent)
    serializer = ProductCategorySerializer(child)
    assert serializer.data["parent_name"] == "Vyakula"
