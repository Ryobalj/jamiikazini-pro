# agriculture/models/harvest_contract.py

from decimal import Decimal
from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.business import Business
from jamiiwallet.models.escrow_hold import EscrowHold

# Uzito uliopokewa ukitofautiana na uliotangazwa kwa zaidi ya asilimia hii,
# malipo hayatolewi kiotomatiki - inaingia DISPUTED kwa utatuzi wa admin.
WEIGHT_TOLERANCE_PERCENT = Decimal("2.00")

# Sehemu ya HOLD (deposit) inayotolewa wakati mkataba unakubaliwa - sehemu
# iliyobaki inalipwa (au inarejeshwa) baada ya uzito halisi kuthibitishwa.
DEPOSIT_PERCENT = Decimal("30.00")


class HarvestContractStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    ACCEPTED = "ACCEPTED", _("Accepted")
    SETTLED = "SETTLED", _("Settled")
    DISPUTED = "DISPUTED", _("Disputed")
    CANCELLED = "CANCELLED", _("Cancelled")


class HarvestContract(UUIDModel, TimeStampedModel):
    """
    Mkataba wa awali wa mazao (forward contract) - bei ya kila kilo inakubaliwa
    kabla mavuno hayajawepo, lakini malipo ya mwisho yanategemea UZITO HALISI
    utakaopimwa wakati wa kupokea (delivered_weight), si kiasi kilichokadiriwa
    mwanzoni. Hii ni tofauti kubwa na Product/Order ya kawaida (bei imefungwa
    tangu mwanzoni) - jambo geni kabisa lililoongezwa kwa awamu hii.

    Mtiririko: PENDING (mnunuzi ametangaza) -> ACCEPTED (muuzaji amedai, HOLD
    ya 30% ya kiasi kilichokadiriwa imeshikiliwa) -> pande zote mbili
    zinathibitisha uzito halisi kwa kujitegemea -> zikilingana (ndani ya
    asilimia 2) -> SETTLED (malipo kamili yanatolewa); zisipolingana ->
    DISPUTED (fedha zinabaki zimeshikiliwa, admin anaingilia kati kimkono -
    hakuna mfumo wa kiotomatiki wa kutatua mizozo bado).
    """
    buyer = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="harvest_contracts_as_buyer",
    )
    seller = models.ForeignKey(
        Business, null=True, blank=True, on_delete=models.SET_NULL, related_name="harvest_contracts_as_seller",
    )

    crop_description = models.CharField(max_length=255)
    estimated_weight_kg = models.DecimalField(max_digits=12, decimal_places=3)
    agreed_price_per_kg = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_window_start = models.DateField()
    delivery_window_end = models.DateField()

    status = models.CharField(
        max_length=10, choices=HarvestContractStatus.choices, default=HarvestContractStatus.PENDING,
    )

    escrow_hold = models.ForeignKey(
        EscrowHold, null=True, blank=True, on_delete=models.SET_NULL, related_name="harvest_contract",
    )

    buyer_confirmed_weight = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    buyer_confirmed_at = models.DateTimeField(null=True, blank=True)
    seller_confirmed_weight = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    seller_confirmed_at = models.DateTimeField(null=True, blank=True)

    settled_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Harvest Contract")
        verbose_name_plural = _("Harvest Contracts")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"HarvestContract({self.crop_description}, {self.estimated_weight_kg}kg, {self.status})"

    @property
    def estimated_total(self):
        return self.estimated_weight_kg * self.agreed_price_per_kg

    @property
    def deposit_amount(self):
        return (self.estimated_total * DEPOSIT_PERCENT / Decimal("100")).quantize(Decimal("0.01"))

    def both_weights_confirmed(self):
        return bool(self.buyer_confirmed_weight is not None and self.seller_confirmed_weight is not None)

    def weights_match_within_tolerance(self):
        if not self.both_weights_confirmed():
            return False
        larger = max(self.buyer_confirmed_weight, self.seller_confirmed_weight)
        if larger == 0:
            return self.buyer_confirmed_weight == self.seller_confirmed_weight
        diff_percent = abs(self.buyer_confirmed_weight - self.seller_confirmed_weight) / larger * Decimal("100")
        return diff_percent <= WEIGHT_TOLERANCE_PERCENT
