# billpay/models/biller.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from gov_integration.models.country_config import CountryConfig


class BillerCategory(models.TextChoices):
    ELECTRICITY = "ELECTRICITY", _("Electricity")
    AIRTIME = "AIRTIME", _("Airtime")
    TV = "TV", _("TV Subscription")
    WATER = "WATER", _("Water")


class Biller(UUIDModel, TimeStampedModel):
    """
    Muuzaji wa huduma (LUKU, airtime, DSTV, maji, n.k.). `config_key` inaunganisha
    na jamiikazini/settings/billpay_api_config.py (env-var driven, sawa kabisa na
    gov_api_config.py) badala ya kuandika mantiki maalum ya kila nchi/mamlaka
    kwenye code - kuongeza mamlaka mpya ni suala la env vars + rekodi mpya ya
    Biller, si mabadiliko ya code.
    """
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=BillerCategory.choices)
    country = models.ForeignKey(
        CountryConfig, on_delete=models.PROTECT, related_name="billers",
    )
    config_key = models.CharField(
        max_length=50,
        help_text=_("Jina la config kwenye billpay_api_config.py, mf. 'TZ_LUKU'."),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Biller")
        verbose_name_plural = _("Billers")
        unique_together = ("country", "config_key")
        ordering = ["country", "category", "name"]

    def __str__(self):
        return f"{self.name} ({self.country.code})"
