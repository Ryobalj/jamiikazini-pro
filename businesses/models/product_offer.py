# businesses/models/product_offer.py

from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.product import Product


class ProductOfferStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    ACCEPTED = "ACCEPTED", _("Accepted")
    REJECTED = "REJECTED", _("Rejected")
    COUNTERED = "COUNTERED", _("Countered")
    EXPIRED = "EXPIRED", _("Expired")


class ProductOffer(UUIDModel, TimeStampedModel):
    """
    Ofa ya bei kutoka kwa mnunuzi kwa bidhaa fulani (kama utaratibu wa
    kujadiliana bei - kawaida sokoni kama Kariakoo). Imefungwa kwenye "duru
    moja" ya majadiliano: mnunuzi anatoa ofa -> muuzaji anakubali/anakataa/
    anatoa ofa mbadala -> ikiwa ofa mbadala, mnunuzi anakubali/anakataa
    (mwisho, hakuna majadiliano zaidi baada ya hapo). Muundo huu unafuata
    logistics.models.fare_proposal.FareProposal (status enum + accept/reject/
    counter), lakini kwa bidhaa badala ya bei ya usafiri.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="offers")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="product_offers")
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("1.000"))
    proposed_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    counter_unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=ProductOfferStatus.choices, default=ProductOfferStatus.PENDING)
    # Set True once an Order has been placed against an ACCEPTED offer -
    # prevents reusing the same negotiated price for a second order.
    consumed = models.BooleanField(default=False)
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = _("Product Offer")
        verbose_name_plural = _("Product Offers")
        ordering = ["-created_at"]

    @property
    def accepted_unit_price(self):
        """The price the buyer actually agreed to pay, whichever round it was settled at."""
        return self.counter_unit_price if self.counter_unit_price is not None else self.proposed_unit_price

    def __str__(self):
        return f"ProductOffer({self.product_id}) by {self.buyer} - {self.proposed_unit_price} [{self.status}]"
