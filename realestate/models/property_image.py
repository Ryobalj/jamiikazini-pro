# realestate/models/property_image.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from kiini.models.base import UUIDModel, TimeStampedModel
from realestate.models.property_listing import PropertyListing


class PropertyImage(UUIDModel, TimeStampedModel):
    """Picha za tangazo, zenye mpangilio (order) - tofauti na Product.additional_images
    (URL array tu), hii ni model kamili kwa sababu kuvinjari mali isiyohamishika
    hutegemea sana picha nyingi zenye mpangilio mzuri."""
    property = models.ForeignKey(
        PropertyListing, on_delete=models.CASCADE, related_name="images",
    )
    image = models.ImageField(upload_to="properties/images/")
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Property Image")
        verbose_name_plural = _("Property Images")
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Image for {self.property_id} (#{self.order})"
