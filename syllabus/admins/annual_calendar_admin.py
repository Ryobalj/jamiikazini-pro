# syllabus/admins/annual_calendar_admin.py

from django.contrib import admin
from syllabus.models.annual_calendar import AnnualCalendar


@admin.register(AnnualCalendar)
class AnnualCalendarAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "institute",
        "year",
        "total_learning_days",
        "status",
        "term_start_date",
        "midterm_break_start_date",
        "midterm_start_date",
        "term_break_start_date",
        "annual_startdate",
        "midannual_break_start_date",
        "midannual_start_date",
        "annual_break_start_date",
    )

    list_filter = ("status", "year", "institute")
    search_fields = ("institute",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("year", "institute")

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "institute",
                "year",
                "total_learning_days",
                "status",
            )
        }),

        ("Term 1 Start", {
            "fields": (
                "term_start_month",
                "term_start_week",
                "term_start_date",
            )
        }),

        ("Midterm Break Start", {
            "fields": (
                "midterm_break_start_month",
                "midterm_break_start_week",
                "midterm_break_start_date",
            )
        }),

        ("Midterm Start", {
            "fields": (
                "midterm_start_month",
                "midterm_start_week",
                "midterm_start_date",
            )
        }),

        ("Term Break Start", {
            "fields": (
                "term_break_start_month",
                "term_break_start_week",
                "term_break_start_date",
            )
        }),

        ("Annual Start", {
            "fields": (
                "annual_startmonth",
                "annual_startweek",
                "annual_startdate",
            )
        }),

        ("Midannual Break Start", {
            "fields": (
                "midannual_break_start_month",
                "midannual_break_start_week",
                "midannual_break_start_date",
            )
        }),

        ("Midannual Start", {
            "fields": (
                "midannual_start_month",
                "midannual_start_week",
                "midannual_start_date",
            )
        }),

        ("Annual Break Start", {
            "fields": (
                "annual_break_start_month",
                "annual_break_start_week",
                "annual_break_start_date",
            )
        }),

        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )