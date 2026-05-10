# syllabus/tests/test_admin/test_annual_calendar_admin.py

import pytest
from django.contrib.admin.sites import AdminSite
from syllabus.admins.annual_calendar_admin import AnnualCalendarAdmin
from syllabus.models.annual_calendar import AnnualCalendar

@pytest.mark.django_db
class TestAnnualCalendarAdmin:

    def test_admin_registration(self):
        """
        Hakikisha AnnualCalendar ime-register kwenye admin site
        """
        site = AdminSite()
        admin_instance = AnnualCalendarAdmin(AnnualCalendar, site)
        assert isinstance(admin_instance, AnnualCalendarAdmin)

    def test_list_display_fields(self):
        site = AdminSite()
        admin_instance = AnnualCalendarAdmin(AnnualCalendar, site)
        expected_fields = (
            "id",
            "institute",
            "year",
            "total_learning_days",
            "status",
            "term_start_date",
            "midannual_start_date",
            "annual_break_start_date",
        )
        assert admin_instance.list_display == expected_fields

    def test_list_filter_fields(self):
        site = AdminSite()
        admin_instance = AnnualCalendarAdmin(AnnualCalendar, site)
        assert admin_instance.list_filter == ("status", "year", "institute")

    def test_search_fields(self):
        site = AdminSite()
        admin_instance = AnnualCalendarAdmin(AnnualCalendar, site)
        assert admin_instance.search_fields == ("institute",)

    def test_readonly_fields(self):
        site = AdminSite()
        admin_instance = AnnualCalendarAdmin(AnnualCalendar, site)
        assert admin_instance.readonly_fields == ("id", "created_at", "updated_at")

    def test_ordering(self):
        site = AdminSite()
        admin_instance = AnnualCalendarAdmin(AnnualCalendar, site)
        assert admin_instance.ordering == ("year", "institute")

    def test_fieldsets_structure(self):
        site = AdminSite()
        admin_instance = AnnualCalendarAdmin(AnnualCalendar, site)
        # Hakikisha kila fieldset ina jina na fields
        for name, opts in admin_instance.fieldsets:
            assert "fields" in opts
            assert isinstance(opts["fields"], tuple)