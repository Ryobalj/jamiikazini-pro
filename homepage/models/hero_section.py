# homepage/models/hero_section.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel


class HeroSection(UUIDModel, TimeStampedModel):
    """Banner kuu ya juu ya homepage."""

    homepage = models.ForeignKey(
        'homepage.HomePage', on_delete=models.CASCADE, related_name='hero_sections'
    )

    title = models.CharField(max_length=200)
    subtitle = models.TextField(blank=True)
    background_image = models.ImageField(upload_to='homepage/hero/', blank=True, null=True)

    cta_text = models.CharField(max_length=50, blank=True, default=_('Wasiliana Nasi'))
    cta_link = models.CharField(max_length=200, blank=True, default='#contact')

    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _('Hero Section')
        verbose_name_plural = _('Hero Sections')

    def __str__(self):
        return self.title[:50]
