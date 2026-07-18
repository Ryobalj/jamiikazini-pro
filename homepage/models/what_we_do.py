# homepage/models/what_we_do.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel


class WhatWeDo(UUIDModel, TimeStampedModel):
    """Sehemu ya 'Tunachofanya' - muhtasari wa huduma/bidhaa kuu."""

    homepage = models.ForeignKey(
        'homepage.HomePage', on_delete=models.CASCADE, related_name='what_we_do_sections'
    )

    title = models.CharField(max_length=200, default=_('Tunachofanya'))
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='homepage/whatwedo/', blank=True, null=True)

    cta_text = models.CharField(max_length=50, blank=True, default=_('Jifunze Zaidi'))
    cta_link = models.CharField(max_length=200, blank=True)

    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _('What We Do Section')
        verbose_name_plural = _('What We Do Sections')

    def __str__(self):
        return self.title[:50]

    def get_services(self):
        return self.services.filter(is_active=True).order_by('order', 'id')

    def get_related_images(self):
        return self.related_images.filter(is_active=True).order_by('order', '-created_at')


class WhatWeDoService(UUIDModel, TimeStampedModel):
    """Kipengele kimoja (huduma/bidhaa) ndani ya WhatWeDo grid."""

    what_we_do = models.ForeignKey(WhatWeDo, on_delete=models.CASCADE, related_name='services')
    icon = models.CharField(max_length=50, blank=True, help_text=_('Jina la icon, mfano: truck, heart'))
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = _('What We Do Service')
        verbose_name_plural = _('What We Do Services')

    def __str__(self):
        return self.title


class WhatWeDoImage(UUIDModel, TimeStampedModel):
    """Picha za ziada (gallery) za WhatWeDo."""

    what_we_do = models.ForeignKey(WhatWeDo, on_delete=models.CASCADE, related_name='related_images')
    image = models.ImageField(upload_to='homepage/whatwedo/gallery/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _('What We Do Image')
        verbose_name_plural = _('What We Do Images')

    def __str__(self):
        return f'Image for {self.what_we_do.title} ({self.caption or "no caption"})'
