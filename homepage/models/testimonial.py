# homepage/models/testimonial.py

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel


class Testimonial(UUIDModel, TimeStampedModel):
    """Maoni ya mteja yanayoonekana kwenye homepage."""

    homepage = models.ForeignKey('homepage.HomePage', on_delete=models.CASCADE, related_name='testimonials')

    client_name = models.CharField(max_length=150)
    client_role = models.CharField(max_length=150, blank=True)
    client_image = models.ImageField(upload_to='homepage/testimonials/', blank=True, null=True)

    content = models.TextField()
    rating = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _('Testimonial')
        verbose_name_plural = _('Testimonials')

    def __str__(self):
        return f'{self.client_name} - {self.rating}★'
