# businesses/tests/test_models/test_product_category.py

import pytest
from businesses.models.product_category import ProductCategory

pytestmark = pytest.mark.django_db


class TestProductCategoryModel:
    def test_string_representation(self):
        category = ProductCategory.objects.create(name="Vyakula", slug="vyakula")
        assert str(category) == "Vyakula"

    def test_verbose_names(self):
        field_verbose = {
            "name": "Category Name",
            "slug": "Slug",
            "description": "Description",
        }
        for field, expected in field_verbose.items():
            assert ProductCategory._meta.get_field(field).verbose_name == expected

    def test_ordering(self):
        ProductCategory.objects.create(name="Zed", slug="zed")
        ProductCategory.objects.create(name="Alpha", slug="alpha")
        categories = list(ProductCategory.objects.all())
        assert categories[0].name == "Alpha"
        assert categories[1].name == "Zed"

    def test_description_optional(self):
        category = ProductCategory.objects.create(name="Elektroniki", slug="elektroniki")
        assert category.description in (None, "")

    def test_parent_child_hierarchy(self):
        parent = ProductCategory.objects.create(name="Vyakula", slug="vyakula")
        child = ProductCategory.objects.create(name="Nafaka", slug="nafaka", parent=parent)
        assert child.parent == parent
        assert child.parent_name == "Vyakula"
        assert parent.children_count() == 1

    def test_parent_name_defaults_when_no_parent(self):
        category = ProductCategory.objects.create(name="Vyakula", slug="vyakula")
        assert category.parent_name == "---"
