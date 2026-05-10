from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.contrib.gis.forms.widgets import OSMWidget
from django.utils.translation import gettext_lazy as _
from ..models.institution import Institution


@admin.register(Institution)
class InstitutionAdmin(GISModelAdmin):
    list_display = (
        "name",
        "domain",
        "institution_type",
        "tier",
        "owner",
        "phone",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "tier", "institution_type")
    search_fields = ("name", "domain", "email", "phone", "owner__username")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at", "owner")
    ordering = ("name",)

    fieldsets = (
        (_("Basic Info"), {
            "fields": ("name", "domain", "institution_type", "tier", "owner")
        }),
        (_("Contact Info"), {
            "fields": ("email", "phone", "address")
        }),
        (_("Location"), {
            "fields": ("location",)
        }),
        (_("Status & Metadata"), {
            "fields": ("is_active", "metadata")
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at")
        }),
    )

    formfield_overrides = {
        # Customize location field to use OSMWidget with zoom & default location
        # Adjust longitude and latitude accordingly
        Institution._meta.get_field('location'): {
            'widget': OSMWidget(attrs={
                'map_width': 800,
                'map_height': 500,
                'default_lon': 39.2083,    # Tanzania approx longitude
                'default_lat': -6.7924,    # Tanzania approx latitude
                'default_zoom': 6,
            })
        }
    }