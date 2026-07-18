# businesses/models/import_request.py

from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from accounts.models import User
from businesses.models.business import Business
from businesses.models.order import Order


class ImportRequestStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CLAIMED = "CLAIMED", _("Claimed")
    FULFILLED = "FULFILLED", _("Fulfilled")
    EXPIRED = "EXPIRED", _("Expired")
    CANCELLED = "CANCELLED", _("Cancelled")


class ImportRequest(UUIDModel, TimeStampedModel):
    """
    Ombi la mnunuzi la kutafuta mfanyabiashara anayeweza kumwagizia bidhaa
    kutoka nje ya nchi (sourcing/quote-request) - biashara zilizojiwekea
    deals_in_imports=True zinaona ombi na kudai (claim) kwa kutoa bei na
    makadirio ya muda. Hii SI mfumo wa forodha/usafirishaji - ni soko la
    kuunganisha mnunuzi na muagizaji tu.
    """
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="import_requests",
        verbose_name=_("Buyer"),
    )
    item_description = models.TextField(
        verbose_name=_("Item Description"),
        help_text=_("Maelezo ya bidhaa inayotakiwa kuagizwa - jina, aina, spesifikesheni."),
    )
    # Free text (mf. "China", "Dubai", "Uturuki") - nchi za asili ya bidhaa
    # zinazoagizwa ziko nje ya orodha ya nchi za EAC zilizo kwenye
    # gov_integration.CountryConfig, hivyo FK haiwezi kutumika hapa.
    origin_country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Origin Country"),
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("1.000"))
    budget_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Budget Amount"),
    )
    budget_currency = models.ForeignKey(
        "payments.Currency",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="import_requests",
    )
    status = models.CharField(
        max_length=20,
        choices=ImportRequestStatus.choices,
        default=ImportRequestStatus.PENDING,
    )
    claimed_by_business = models.ForeignKey(
        Business,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="claimed_import_requests",
    )
    # Bei aliyotoa muagizaji, ikiwa imebadilishwa kuwa sarafu ya msingi (TZS)
    # kupitia currency_service.convert() kama alinukuu kwa sarafu ya kigeni.
    claimed_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Claimed Price"),
    )
    estimated_lead_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Estimated Lead Days"),
        help_text=_("Makadirio ya siku za kusubiri bidhaa ifike - si ufuatiliaji halisi wa usafirishaji."),
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    order = models.OneToOneField(
        Order,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="import_request",
    )

    class Meta:
        verbose_name = _("Import Request")
        verbose_name_plural = _("Import Requests")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"ImportRequest({self.item_description[:40]}) by {self.buyer.email} - {self.status}"
