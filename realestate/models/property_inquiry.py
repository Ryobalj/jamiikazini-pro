# realestate/models/property_inquiry.py

from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from realestate.models.property_listing import PropertyListing
from jamiiwallet.models.escrow_hold import EscrowHold


class PropertyInquiryStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")       # buyer amependekeza nia, hakuna malipo bado
    RESERVED = "RESERVED", _("Reserved")    # amelipa (HOLD), tangazo halionekani tena
    COMPLETED = "COMPLETED", _("Completed")  # handover imekamilika, fedha zimetolewa
    CANCELLED = "CANCELLED", _("Cancelled")
    REJECTED = "REJECTED", _("Rejected")


class PropertyInquiry(UUIDModel, TimeStampedModel):
    """
    Mnunuzi/mpangaji anaonyesha nia (PENDING, bure), kisha akitaka kudhibitisha
    anachukua (reserve) analipa (RESERVED - HOLD ya EscrowHold, tangazo
    linaondolewa kwenye orodha ya umma mara moja). Handover inahitaji
    uthibitisho wa pande zote mbili (buyer_confirmed_at + owner_confirmed_at) -
    sawa na jinsi delivery escrow inavyohitaji buyer na dereva wote
    kuthibitisha - ndipo fedha zinatolewa (CAPTURE) kwa mmiliki.
    """
    property = models.ForeignKey(
        PropertyListing, on_delete=models.CASCADE, related_name="inquiries",
    )
    buyer = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="property_inquiries",
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=PropertyInquiryStatus.choices, default=PropertyInquiryStatus.PENDING,
    )

    escrow_hold = models.ForeignKey(
        EscrowHold, null=True, blank=True, on_delete=models.SET_NULL, related_name="property_inquiry",
    )
    reserved_at = models.DateTimeField(null=True, blank=True)
    buyer_confirmed_at = models.DateTimeField(null=True, blank=True)
    owner_confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Property Inquiry")
        verbose_name_plural = _("Property Inquiries")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"Inquiry({self.property_id}, {self.buyer.email}, {self.status})"

    def is_handover_ready(self):
        # NB: hatuwezi kutumia @property hapa - jina la field `property`
        # (FK) linaficha decorator ya @property ndani ya class body hii.
        return bool(self.buyer_confirmed_at and self.owner_confirmed_at)
