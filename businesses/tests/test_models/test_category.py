# businesses/tests/test_models/test_category.py

import pytest
from businesses.models.category import BusinessCategory

pytestmark = pytest.mark.django_db

class TestBusinessCategoryModel:
    def test_string_representation(self):
        category = BusinessCategory.objects.create(name="Retail", slug="retail")
        assert str(category) == "Retail"

    def test_verbose_names(self):
        field_verbose = {
            "name": "Category Name",
            "slug": "Slug",
            "description": "Description",
        }
        for field, expected in field_verbose.items():
            assert BusinessCategory._meta.get_field(field).verbose_name == expected

    def test_ordering(self):
        BusinessCategory.objects.create(name="Zed", slug="zed")
        BusinessCategory.objects.create(name="Alpha", slug="alpha")
        categories = list(BusinessCategory.objects.all())
        assert categories[0].name == "Alpha"
        assert categories[1].name == "Zed"

    def test_description_optional(self):
        category = BusinessCategory.objects.create(name="Tech", slug="tech")
        assert category.description in (None, "")