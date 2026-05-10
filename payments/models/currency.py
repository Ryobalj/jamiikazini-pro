# payments/models/currency.py

from django.db import models
from django.utils.translation import gettext_lazy as _

class Currency(models.Model):
    """
    Model ya kuwakilisha currencies zinazotumika Jamiikazini (EAC region + mashuhuri).
    """

    CURRENCY_CHOICES = [
        ("TZS", _("Tanzanian Shilling")),
        ("KES", _("Kenyan Shilling")),
        ("UGX", _("Ugandan Shilling")),
        ("RWF", _("Rwandan Franc")),
        ("BIF", _("Burundi Franc")),
        ("USD", _("US Dollar")),
        ("EUR", _("Euro")),
        ("GBP", _("British Pound")),
    ]

    SYMBOL_MAP = {
        "TZS": "Tsh",
        "KES": "KSh",
        "UGX": "USh",
        "RWF": "FRw",
        "BIF": "FBu",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
    }

    COUNTRY_MAP = {
        "TZS": _("Tanzania"),
        "KES": _("Kenya"),
        "UGX": _("Uganda"),
        "RWF": _("Rwanda"),
        "BIF": _("Burundi"),
        "USD": _("United States"),
        "EUR": _("European Union"),
        "GBP": _("United Kingdom"),
    }

    code = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        unique=True,
        help_text=_("Currency code (ISO 4217) ya fedha.")
    )
    name = models.CharField(max_length=64, editable=False)
    symbol = models.CharField(max_length=8, editable=False)
    country = models.CharField(max_length=64, blank=True, null=True, help_text=_("Nchi inayotumia currency hii."))

    is_active = models.BooleanField(default=True, help_text=_("Ikiwa currency bado inatumika."))

    exchange_rate_to_tzs = models.DecimalField(
        max_digits=12, decimal_places=6, null=True, blank=True,
        help_text=_("Kiwango cha kubadilisha fedha kulinganisha na TZS.")
    )

    class Meta:
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.symbol})"

    def save(self, *args, **kwargs):
        self.name = dict(self.CURRENCY_CHOICES).get(self.code, "")
        self.symbol = self.SYMBOL_MAP.get(self.code, "")
        if not self.country:
            self.country = self.COUNTRY_MAP.get(self.code, "")
        super().save(*args, **kwargs)

    @classmethod
    def get_by_code(cls, code="TZS"):
        """Return Currency instance by code, or create default TZS if not exists."""
        try:
            return cls.objects.get(code=code)
        except cls.DoesNotExist:
            tzs, created = cls.objects.get_or_create(
                code="TZS",
                defaults={"is_active": True}
            )
            return tzs