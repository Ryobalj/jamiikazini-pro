# businesses/models/product_price_tier.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.product import Product


class ProductPriceTier(UUIDModel, TimeStampedModel):
    """
    Bei ya jumla (wholesale) kwa kiasi fulani cha bidhaa - mf. TSh 18/kg
    ukinunua kilo 500+, badala ya bei ya kawaida TSh 20/kg. Inatumika na
    Product.price_for_quantity() - haitegemei aina ya mnunuzi (mtu binafsi au
    biashara), yeyote anayenunua kiasi kikubwa cha kutosha anapata bei hii.
    min_quantity ya tier NDIYO wingi wa chini unaohitajika (MOQ) - hakuna field
    tofauti ya MOQ.
    """
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="price_tiers",
        verbose_name=_("Product"),
    )
    min_quantity = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name=_("Minimum Quantity"),
        help_text=_("Kiasi cha chini (MOQ) kinachohitajika kupata bei hii."),
    )
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Unit Price"),
        help_text=_("Bei ya kitengo kimoja ukinunua angalau min_quantity."),
    )

    class Meta:
        verbose_name = _("Product Price Tier")
        verbose_name_plural = _("Product Price Tiers")
        ordering = ["min_quantity"]
        constraints = [
            models.UniqueConstraint(fields=["product", "min_quantity"], name="unique_tier_per_quantity"),
        ]

    def __str__(self):
        return f"{self.product.name}: {self.unit_price}/unit @ {self.min_quantity}+"
