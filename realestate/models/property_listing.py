# realestate/models/property_listing.py

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.business import Business
from payments.models.currency import Currency


class PropertyListingType(models.TextChoices):
    RENT = "RENT", _("For Rent")
    SALE = "SALE", _("For Sale")


class PropertyType(models.TextChoices):
    LAND = "LAND", _("Land")
    HOUSE = "HOUSE", _("House")
    APARTMENT = "APARTMENT", _("Apartment")
    COMMERCIAL = "COMMERCIAL", _("Commercial")


class PropertyStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", _("Available")
    RESERVED = "RESERVED", _("Reserved")
    RENTED = "RENTED", _("Rented")
    SOLD = "SOLD", _("Sold")


class PropertyListing(UUIDModel, TimeStampedModel):
    """
    Tangazo la mali isiyohamishika (nyumba, kiwanja, ofisi) - kwa kukodisha au
    kuuza. `owner` ni Business (mmiliki/dalali lazima ajisajili kama biashara
    kwanza, akitumia uthibitisho uliopo). `title_deed_number` ni ya kutolewa
    na muuzaji tu - HAKUNA uunganisho na ardhi.go.tz au usajili wowote wa
    serikali (haupo kwenye mfumo huu), hivyo ni taarifa ya kujiamini tu, si
    uthibitisho rasmi wa umiliki.

    `status` ni lango kuu la "kutoonekana tena baada ya kuchukuliwa": list na
    utafutaji wote hutumia status=AVAILABLE pekee - mara RESERVED/RENTED/SOLD,
    tangazo halionekani tena kwenye orodha ya umma.
    """
    owner = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="property_listings",
    )
    listing_type = models.CharField(max_length=10, choices=PropertyListingType.choices)
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)

    location = gis_models.PointField(geography=True)
    address_text = models.CharField(max_length=255, blank=True)

    # RENT: bei ya kila mwezi. SALE: bei ya jumla, mara moja.
    price = models.DecimalField(max_digits=14, decimal_places=2)
    # RENT pekee - kiasi cha ziada (mf. amana) kinachoshikiliwa pamoja na mwezi
    # wa kwanza wakati wa kuchukua (reserve). SALE haihitaji hii (bei yote
    # moja tayari iko kwenye `price`).
    deposit_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="property_listings")

    lease_duration_months = models.PositiveIntegerField(null=True, blank=True)
    bedrooms = models.PositiveIntegerField(null=True, blank=True)
    bathrooms = models.PositiveIntegerField(null=True, blank=True)
    size_sqm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)

    title_deed_number = models.CharField(
        max_length=100, blank=True,
        help_text=_("Namba ya hati - imetolewa na muuzaji mwenyewe, HAIJATHIBITISHWA na ardhi.go.tz."),
    )

    status = models.CharField(
        max_length=10, choices=PropertyStatus.choices, default=PropertyStatus.AVAILABLE,
    )

    class Meta:
        verbose_name = _("Property Listing")
        verbose_name_plural = _("Property Listings")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["listing_type", "property_type"]),
        ]

    def __str__(self):
        return f"{self.get_property_type_display()} ({self.get_listing_type_display()}) - {self.owner.name}"

    @property
    def reservation_amount(self):
        """Kiasi kitakachoshikiliwa (HOLD) wakati wa kuchukua (reserve)."""
        if self.listing_type == PropertyListingType.RENT:
            return self.price + (self.deposit_amount or 0)
        return self.price
