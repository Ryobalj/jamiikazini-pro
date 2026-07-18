from django.contrib import admin

from realestate.models.property_listing import PropertyListing
from realestate.models.property_image import PropertyImage
from realestate.models.property_inquiry import PropertyInquiry


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0


@admin.register(PropertyListing)
class PropertyListingAdmin(admin.ModelAdmin):
    list_display = ("owner", "listing_type", "property_type", "price", "status", "created_at")
    list_filter = ("listing_type", "property_type", "status")
    search_fields = ("address_text", "title_deed_number")
    inlines = [PropertyImageInline]


@admin.register(PropertyInquiry)
class PropertyInquiryAdmin(admin.ModelAdmin):
    list_display = ("property", "buyer", "status", "reserved_at", "completed_at")
    list_filter = ("status",)
    readonly_fields = ("escrow_hold",)
