# businesses/models/product_image.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.product import Product


class ProductImage(UUIDModel, TimeStampedModel):
    """Picha za ziada za bidhaa, zenye mpangilio (order) - inachukua nafasi ya
    Product.additional_images (URL array tu), sawa na jinsi PropertyImage
    inavyofanya kazi kwa PropertyListing (angalia realestate/models/property_image.py)."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images",
    )
    image = models.ImageField(upload_to="products/gallery/")
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.product_id} (#{self.order})"
