# businesses/models/product.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from django.utils.text import slugify

from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.business import Business
from businesses.models.product_category import ProductCategory


class ProductType(models.TextChoices):
    PHYSICAL = "physical", _("Physical")
    DIGITAL = "digital", _("Digital")
    SERVICE = "service", _("Service")


class UnitChoices(models.TextChoices):
    PIECES = "pcs", _("Pieces")
    KILOGRAMS = "kg", _("Kilograms")
    GRAMS = "g", _("Grams")
    LITRES = "l", _("Litres")
    MILLILITRES = "ml", _("Millilitres")
    BOX = "box", _("Box")
    PACK = "pack", _("Pack")
    DOZEN = "dozen", _("Dozen")
    PAIR = "pair", _("Pair")
    SET = "set", _("Set")
    METER = "m", _("Meter")
    CENTIMETER = "cm", _("Centimeter")
    HOUR = "hour", _("Hour")
    DAY = "day", _("Day")
    SESSION = "session", _("Session")
    # Informal trading units common in wholesale markets like Kariakoo.
    GUNIA = "gunia", _("Gunia (Sack)")
    DEBE = "debe", _("Debe (~20L Tin)")
    FUNGU = "fungu", _("Fungu (Bundle)")
    ROLI = "roli", _("Roli (Roll)")
    BALE = "bale", _("Bale (Mtumba)")


# Units that don't make sense fractionally (you can't buy 2.5 pieces or 1.5 boxes)
WHOLE_UNIT_TYPES = {
    UnitChoices.PIECES, UnitChoices.BOX, UnitChoices.PACK,
    UnitChoices.DOZEN, UnitChoices.PAIR, UnitChoices.SET, UnitChoices.SESSION,
    UnitChoices.GUNIA, UnitChoices.DEBE, UnitChoices.FUNGU,
    UnitChoices.ROLI, UnitChoices.BALE,
}


class LanguageChoices(models.TextChoices):
    SWAHILI = "sw", _("Swahili")
    ENGLISH = "en", _("English")
    FRENCH = "fr", _("French")
    ARABIC = "ar", _("Arabic")


class Product(UUIDModel, TimeStampedModel):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("Business"),
        help_text=_("Biashara inayomiliki bidhaa hii.")
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("Product Name"),
        help_text=_("Jina la bidhaa.")
    )

    slug = models.SlugField(
        unique=True,
        max_length=300,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly identifier ya bidhaa.")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Maelezo ya bidhaa hii.")
    )

    type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.PHYSICAL,
        verbose_name=_("Product Type"),
        help_text=_("Aina ya bidhaa: Physical, Digital, au Service.")
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Price"),
        help_text=_("Bei ya kawaida ya bidhaa.")
    )

    discount_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Discount Price"),
        help_text=_("Bei ya punguzo ikiwa ipo.")
    )

    currency = models.ForeignKey(
        'payments.Currency',
        on_delete=models.PROTECT,
        related_name='products',
        null=True,
        blank=True,
        verbose_name=_("Currency"),
        help_text=_("Sarafu ya bei ya bidhaa.")
    )

    quantity_in_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name=_("Stock Quantity"),
        help_text=_("Idadi ya bidhaa zilizopo stock (inaweza kuwa na desimali kwa vipimo kama kg, l, m).")
    )

    unit = models.CharField(
        max_length=20,
        choices=UnitChoices.choices,
        default=UnitChoices.PIECES,
        verbose_name=_("Unit"),
        help_text=_("Kipimo cha bidhaa.")
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name=_("Is Available"),
        help_text=_("Inaonesha kama bidhaa ipo sokoni au la.")
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Is Featured"),
        help_text=_("Inaonesha kama bidhaa ni ya kipekee (featured).")
    )

    image = models.ImageField(
        upload_to='products/images/',
        null=True,
        blank=True,
        verbose_name=_("Product Image"),
        help_text=_("Picha kuu ya bidhaa.")
    )

    additional_images = ArrayField(
        base_field=models.URLField(),
        blank=True,
        null=True,
        verbose_name=_("Additional Images"),
        help_text=_("Picha nyingine za bidhaa (URL links).")
    )

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_("Category"),
        help_text=_("Aina/kabati la bidhaa hii, mfano: Vyakula, Vinywaji, Nguo.")
    )

    tags = ArrayField(
        base_field=models.CharField(max_length=100),
        blank=True,
        default=list,
        verbose_name=_("Tags / Keywords"),
        help_text=_("Maneno muhimu ya ziada ya kutafutia bidhaa (si badala ya category).")
    )

    tax_inclusive = models.BooleanField(
        default=True,
        verbose_name=_("Price includes VAT"),
        help_text=_("Inaonesha kama bei inajumuisha VAT.")
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Tax Rate (%)"),
        help_text=_("Kiwango cha VAT kilichojumuishwa, kwa asilimia.")
    )

    external_link = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("External Link / Purchase Link"),
        help_text=_("Link ya kununua bidhaa kutoka nje ya mfumo huu (optional).")
    )

    digital_file = models.FileField(
        upload_to='products/files/',
        null=True,
        blank=True,
        verbose_name=_("Digital File"),
        help_text=_("Faili la bidhaa za kidigitali (ikiwa ni Digital Product).")
    )

    # LANGUAGE CODE WITH CHOICES
    language_code = models.CharField(
        max_length=10,
        choices=LanguageChoices.choices,
        default=LanguageChoices.ENGLISH,
        verbose_name=_("Language"),
        help_text=_("Lugha inayotumika kwenye maelezo ya bidhaa.")
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["tags"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.business.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        counter = 1
        original_slug = self.slug
        while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        super().save(*args, **kwargs)

    def final_price(self):
        return self.discount_price if self.discount_price else self.price

    def price_for_quantity(self, quantity):
        """Bei ya kitengo kwa kiasi fulani - hutafuta tier ya bei ya jumla ya
        juu kabisa inayokidhi (min_quantity <= quantity), la sivyo hurudisha
        bei ya kawaida (final_price - inajumuisha discount ikiwa ipo). Wazi
        kwa mnunuzi yeyote (si tu biashara) - MOQ ya kila tier ndiyo lango
        pekee, si aina ya mnunuzi."""
        from decimal import Decimal
        quantity = Decimal(str(quantity))
        tier = self.price_tiers.filter(min_quantity__lte=quantity).order_by("-min_quantity").first()
        return tier.unit_price if tier else self.final_price()

    def has_stock(self):
        return self.quantity_in_stock > 0

    def is_digital(self):
        return self.type == ProductType.DIGITAL

    def is_service(self):
        return self.type == ProductType.SERVICE

    def get_currency_symbol(self):
        return self.currency.symbol if self.currency else "TSh"

    def get_currency_code(self):
        return self.currency.code if self.currency else "TZS"

    def get_language_display_name(self):
        return dict(LanguageChoices.choices).get(self.language_code, self.language_code)

    def get_all_images(self):
        images = []
        if self.image:
            images.append(self.image.url)
        if self.additional_images:
            images.extend(self.additional_images)
        return images