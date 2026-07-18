# businesses/models/business.py

from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from kiini.models.base_entity import AbstractEntity
from kiini.models.institution import Institution
from businesses.models.category import BusinessCategory
from accounts.models import User

# DNS-label-safe: herufi ndogo, namba, na hyphen pekee, si -mwanzoni/-mwishoni,
# hadi herufi 63 (kikomo halisi cha DNS label moja).
_DOMAIN_LABEL_VALIDATOR = RegexValidator(
    regex=r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$",
    message=_("Domain lazima iwe herufi ndogo, namba, na hyphen pekee (mfano: mama-lishe)."),
)

class Business(AbstractEntity):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='businesses',
        verbose_name=_("Institution"),
        help_text=_("Taasisi inayosimamia biashara hii.")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Maelezo mafupi kuhusu biashara.")
    )

    category = models.ForeignKey(
        BusinessCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="businesses",
        verbose_name=_("Business Category"),
        help_text=_("Aina au sekta ya biashara.")
    )

    website = models.URLField(
        blank=True,
        verbose_name=_("Website"),
        help_text=_("Tovuti rasmi ya biashara (kama ipo).")
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Is Verified"),
        help_text=_("Je biashara hii imethibitishwa rasmi?")
    )

    slug = models.SlugField(
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly version of the business name.")
    )

    # Sehemu ya kwanza tu ya subdomain (mfano "mama-lishe"), SIO domain kamili -
    # duka linapatikana kwenye https://<domain>.jamiikazini.com. Tofauti na
    # `website` (URLField ya zamani, isiyohusiana) na `slug` (kwa njia za
    # ndani/path-based, sio subdomain).
    domain = models.CharField(
        max_length=63,
        unique=True,
        null=True,
        blank=True,
        validators=[_DOMAIN_LABEL_VALIDATOR],
        verbose_name=_("Subdomain"),
        help_text=_("Sehemu ya kwanza ya anwani ya duka lako: <domain>.jamiikazini.com"),
    )

    broker_commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
        verbose_name=_("Broker Commission Rate (%)"),
        help_text=_("Asilimia ya kamisheni kwa dalali aliyeleta mnunuzi - 0 (default) "
                    "inamaanisha hakuna kamisheni, kipengele hiki hakina athari kabisa "
                    "mpaka mmiliki wa biashara akiweka kiwango zaidi ya sifuri."),
    )

    # Fingerprint ya kudumu (HMAC-SHA256) ya namba ya leseni ya biashara
    # iliyothibitishwa - unique constraint inazuia biashara mbili tofauti
    # zisitumie leseni moja. Sawa na User.national_id_hash.
    license_number_hash = models.CharField(
        max_length=64, blank=True, null=True, unique=True, editable=False,
    )

    deals_in_imports = models.BooleanField(
        default=False,
        verbose_name=_("Deals in Imports"),
        help_text=_("Biashara hii inaweza kuagiza bidhaa kutoka nje ya nchi - "
                    "itaona maombi ya uagizaji (import requests) kutoka kwa wanunuzi."),
    )

    deals_in_agriculture = models.BooleanField(
        default=False,
        verbose_name=_("Deals in Agriculture"),
        help_text=_("Biashara hii inaweza kusambaza mazao ya kilimo kwa wingi - "
                    "itaona mikataba ya awali ya mazao (harvest contracts) kutoka kwa wanunuzi."),
    )

    class Meta:
        verbose_name = _("Business")
        verbose_name_plural = _("Businesses")
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "biashara"
            slug = base_slug
            suffix = 2
            # slug sasa ni sehemu ya subdomain ya umma (domain), hivyo mgongano
            # (majina mawili yanayofanana) lazima usuluhishwe kiotomatiki badala
            # ya ku-crash na IntegrityError.
            while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            self.slug = slug
        if not self.domain:
            self.domain = self.slug
        super().save(*args, **kwargs)

    @property
    def website_url(self):
        if self.domain:
            return f"https://{self.domain}.{settings.CENTRAL_DOMAIN}"
        return ""

    def __str__(self):
        return self.name