# businesses/tests/test_serializers/test_category_serializer.py

import pytest
from businesses.models.category import BusinessCategory
from businesses.serializers.category_serializer import BusinessCategorySerializer

pytestmark = pytest.mark.django_db


def test_valid_category_serialization():
    category = BusinessCategory.objects.create(
        name="Kliniki",
        slug="kliniki",
        description="Huduma za afya kwa jamii"
    )
    serializer = BusinessCategorySerializer(category)
    data = serializer.data
    assert data["name"] == "Kliniki"
    assert data["slug"] == "kliniki"
    assert data["description"] == "Huduma za afya kwa jamii"


def test_category_serializer_with_missing_name():
    data = {
        "slug": "dukala",
        "description": "Biashara ya rejareja"
    }
    serializer = BusinessCategorySerializer(data=data)
    assert not serializer.is_valid()
    assert "name" in serializer.errors


def test_category_serializer_with_valid_data():
    data = {
        "name": "Duka",
        "slug": "duka",
        "description": "Biashara ya bidhaa mbalimbali"
    }
    serializer = BusinessCategorySerializer(data=data)
    assert serializer.is_valid()
    instance = serializer.save()
    assert instance.name == "Duka"
    assert instance.slug == "duka"