# syllabus/tests/test_admin/test_class_level_admin.py

import pytest
from django.contrib.admin.sites import AdminSite
from syllabus.admins.class_level_admin import ClassLevelAdmin
from syllabus.models.class_level import ClassLevel

@pytest.mark.django_db
class TestClassLevelAdmin:

    def setup_method(self):
        self.site = AdminSite()
        self.admin = ClassLevelAdmin(ClassLevel, self.site)

    def test_list_display(self):
        expected = ("id", "name", "order", "description", "created_at", "updated_at")
        assert self.admin.list_display == expected

    def test_list_filter(self):
        expected = ("name",)
        assert self.admin.list_filter == expected

    def test_search_fields(self):
        expected = ("name", "description")
        assert self.admin.search_fields == expected

    def test_readonly_fields(self):
        expected = ("id", "order", "created_at", "updated_at")
        assert self.admin.readonly_fields == expected

    def test_ordering(self):
        expected = ("order",)
        assert self.admin.ordering == expected

    def test_fieldsets_structure(self):
        fieldsets = dict(self.admin.fieldsets)
        assert "Class Level Info" in fieldsets
        assert "System Fields" in fieldsets

        # Check fields in each fieldset
        assert fieldsets["Class Level Info"]["fields"] == ("name", "description")
        assert fieldsets["System Fields"]["fields"] == ("order", "created_at", "updated_at")

    def test_registered_in_admin_site(self):
        from django.contrib import admin
        assert ClassLevel in admin.site._registry