# businesses/models/review.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.business import Business
from businesses.models.product import Product
from businesses.models.service import Service
from accounts.models import User


class Review(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("User"),
        help_text=_("Mteja anayetoa tathmini hii.")
    )

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="reviews",
        null=True,
        blank=True,
        verbose_name=_("Business"),
        help_text=_("Chagua kama review hii ni ya biashara fulani.")
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        null=True,
        blank=True,
        verbose_name=_("Product"),
        help_text=_("Chagua kama review hii ni ya bidhaa fulani.")
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="reviews",
        null=True,
        blank=True,
        verbose_name=_("Service"),
        help_text=_("Chagua kama review hii ni ya huduma fulani.")
    )

    rating = models.PositiveIntegerField(
        verbose_name=_("Rating"),
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text=_("Chagua alama (1 hadi 5) kulingana na uzoefu wako.")
    )

    content = models.TextField(
        verbose_name=_("Review Content"),
        help_text=_("Andika maoni yako kuhusu huduma/bidhaa/biashara.")
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
    null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)

    content_object = GenericForeignKey('content_type', 'object_id')

    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("Is Approved"),
        help_text=_("Tiki kama review hii imepitishwa na admin.")
    )

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ['-created_at']

    def clean(self):
        """Ensure only one of business, product, or service is reviewed."""
        targets = [self.business, self.product, self.service]
        filled = [target for target in targets if target is not None]

        if len(filled) != 1:
            raise ValidationError(
                _("Tafadhali toa review kwa kitu kimoja tu: biashara, bidhaa, au huduma.")
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def comment(self):
        return self.content
    
    @comment.setter
    def comment(self, value):
        self.content = value

    def __str__(self):
        target = self.service or self.product or self.business
        return f"{self.user.username}'s Review on {target}"
    
