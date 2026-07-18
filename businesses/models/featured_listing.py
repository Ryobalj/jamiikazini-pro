# businesses/models/featured_listing.py

from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.business import Business
from businesses.models.product import Product
from accounts.models import User

DAILY_RATE_TZS = Decimal("2000.00")


class FeaturedPlacement(models.TextChoices):
    HOMEPAGE = "HOMEPAGE", _("Homepage - Bidhaa/Matangazo Yaliyodhaminiwa")


class FeaturedListing(UUIDModel, TimeStampedModel):
    """
    Nafasi ya matangazo iliyolipiwa na biashara ili ionekane kwenye
    sehemu maalum ya jamiikazini homepage (mf. 'Matangazo Yaliyodhaminiwa').
    Inakuwa hai (is_active=True) baada tu ya invoice husika kulipwa.
    """
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="featured_listings",
        verbose_name=_("Business"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="featured_listings",
        null=True,
        blank=True,
        verbose_name=_("Product"),
        help_text=_("Bidhaa maalum ya kutangaza (hiari - kama tupu, biashara nzima ndiyo inayotangazwa)."),
    )
    invoice = models.ForeignKey(
        "payments.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="featured_listings",
        verbose_name=_("Invoice"),
    )
    placement = models.CharField(
        max_length=20,
        choices=FeaturedPlacement.choices,
        default=FeaturedPlacement.HOMEPAGE,
        verbose_name=_("Placement"),
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Amount"),
        help_text=_("Kiasi kilicholipwa/kinachotakiwa kulipwa kwa matangazo haya."),
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name=_("Is Active"),
        help_text=_("Inakuwa True baada ya invoice kulipwa - ndipo inaonekana kwenye homepage."),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="featured_listings_created",
        verbose_name=_("Created By"),
    )

    class Meta:
        verbose_name = _("Featured Listing")
        verbose_name_plural = _("Featured Listings")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "start_date", "end_date"]),
        ]

    def __str__(self):
        return f"{self.business.name} - {self.placement} ({self.start_date} to {self.end_date})"

    @property
    def is_currently_live(self):
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date

    @staticmethod
    def calculate_amount(days: int) -> Decimal:
        return DAILY_RATE_TZS * Decimal(days)
