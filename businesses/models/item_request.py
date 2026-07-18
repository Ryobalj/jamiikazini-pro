# businesses/models/item_request.py

from decimal import Decimal
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from accounts.models import User
from businesses.models.business import Business
from businesses.models.product import Product
from businesses.models.product_category import ProductCategory
from businesses.models.order import Order


class ItemRequestStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CLAIMED = "CLAIMED", _("Claimed")
    FULFILLED = "FULFILLED", _("Fulfilled")
    EXPIRED = "EXPIRED", _("Expired")
    CANCELLED = "CANCELLED", _("Cancelled")


class ItemRequest(UUIDModel, TimeStampedModel):
    """
    Ombi la mnunuzi la kutafuta bidhaa fulani - linatumwa (broadcast) kwa
    biashara za karibu zenye bidhaa hiyo. Biashara ya kwanza kudai (claim)
    ndiyo itakayomhudumia mnunuzi, ili huduma ipatikane hata kama baadhi ya
    biashara hazijibu.
    """
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="item_requests",
        verbose_name=_("Buyer"),
    )
    product_name_query = models.CharField(
        max_length=255,
        verbose_name=_("Search Query"),
        help_text=_("Maneno aliyotafuta mnunuzi - kwa ajili ya rekodi/uchambuzi tu."),
    )
    category = models.ForeignKey(
        ProductCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="item_requests",
    )
    matched_product_ids = ArrayField(
        models.UUIDField(),
        default=list,
        blank=True,
        help_text=_("Snapshot ya Product IDs zilizolingana wakati ombi lilipotumwa."),
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("1.000"))
    location = gis_models.PointField(
        geography=True,
        verbose_name=_("Buyer Location"),
    )
    address_text = models.CharField(max_length=255, blank=True)
    radius_km = models.PositiveIntegerField(default=5)
    status = models.CharField(
        max_length=20,
        choices=ItemRequestStatus.choices,
        default=ItemRequestStatus.PENDING,
    )
    claimed_by_business = models.ForeignKey(
        Business,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="claimed_item_requests",
    )
    claimed_product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="claimed_item_requests",
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    order = models.OneToOneField(
        Order,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="item_request",
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Item Request")
        verbose_name_plural = _("Item Requests")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"ItemRequest({self.product_name_query}) by {self.buyer.email} - {self.status}"
