# logistics/choices.py

from django.utils.translation import gettext_lazy as _
from django.db import models


class TransportTypeChoices(models.TextChoices):
    BODA_BODA = "boda_boda", _("Boda Boda")
    TUK_TUK = "tuk_tuk", _("Tuk Tuk / Bajaji")
    PUBLIC_TRANSPORT = "public_transport", _("Public Transport / Taxi / Suzuki")
    CANTER = "canter", _("Canter")
    FUSO = "fuso", _("Fuso")
    SCANIA = "scania", _("Scania")
    TRAIN = "train", _("Train")
    SHIP = "ship", _("Ship")
    AIR = "air", _("Air Freight")


class TransportRequestStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    ACCEPTED = "accepted", _("Accepted")
    CANCELLED = "cancelled", _("Cancelled")
    EXPIRED = "expired", _("Expired")
