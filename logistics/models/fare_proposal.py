# logistics/models/fare_proposal.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from logistics.models.transport_request import TransportRequest
from logistics.models.transport_provider import TransportProvider
from logistics.models.vehicle import Vehicle


class FareProposalStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    EXPIRED = "EXPIRED", _("Expired")


class FareProposal(UUIDModel, TimeStampedModel):
    """
    Bei mbadala anayopendekeza dereva kwa ombi la usafiri, tofauti na bei
    iliyokadiriwa na mfumo. Haigusi TransportRequest.status - mnunuzi
    anaweza kuikubali baadaye, isipokuwa endapo dereva mwingine tayari
    amekwisha kukubali kwa njia ya haraka (fast-accept).
    """
    transport_request = models.ForeignKey(
        TransportRequest,
        on_delete=models.CASCADE,
        related_name="fare_proposals",
    )
    provider = models.ForeignKey(TransportProvider, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    proposed_fare = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=FareProposalStatus.choices,
        default=FareProposalStatus.PENDING,
    )

    class Meta:
        verbose_name = _("Fare Proposal")
        verbose_name_plural = _("Fare Proposals")
        ordering = ["-created_at"]

    def __str__(self):
        return f"FareProposal({self.transport_request_id}) by {self.provider} - {self.proposed_fare}"
