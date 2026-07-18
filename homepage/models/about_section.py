# homepage/models/about_section.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel


class AboutSection(UUIDModel, TimeStampedModel):
    """Sehemu ya 'Kuhusu Sisi' ya homepage."""

    homepage = models.ForeignKey(
        'homepage.HomePage', on_delete=models.CASCADE, related_name='about_sections'
    )

    title = models.CharField(max_length=200, default=_('Kuhusu Sisi'))
    description = models.TextField()
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    image = models.ImageField(upload_to='homepage/about/', blank=True, null=True)

    stats = models.JSONField(
        default=list, blank=True,
        help_text=_("Orodha ya {number, label}, mfano [{'number': '500+', 'label': 'Wateja'}]")
    )

    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _('About Section')
        verbose_name_plural = _('About Sections')

    def __str__(self):
        return self.title

    def get_gallery(self):
        return self.gallery.filter(is_active=True).order_by('order', '-created_at')


class AboutImage(UUIDModel, TimeStampedModel):
    """Picha za ziada (gallery) za AboutSection."""

    about = models.ForeignKey(AboutSection, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='homepage/about/gallery/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _('About Image')
        verbose_name_plural = _('About Images')

    def __str__(self):
        return f'Image for {self.about.title} ({self.caption or "no caption"})'
