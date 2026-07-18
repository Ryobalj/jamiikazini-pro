# homepage/models/home_page.py

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel

# Model za Django (lowercase) zinazoruhusiwa kuwa "owner" wa HomePage.
ALLOWED_OWNER_MODELS = ('institution', 'business')


class HomePage(UUIDModel, TimeStampedModel):
    """
    Ukurasa mmoja wa umma kwa kila Institution AU Business - toleo la
    multi-tenant la 'SiteSetting' ya feevert-pro. Sections zote (Hero,
    About, WhatWeDo, Faq, Testimonial) zinaunganishwa na HII (si moja kwa
    moja na owner), ili HomePage iwe mzizi mmoja wa uhusiano wote.
    """

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(help_text=_('id ya Institution au Business inayomiliki homepage hii'))
    owner = GenericForeignKey('content_type', 'object_id')

    name = models.CharField(max_length=200, help_text=_('Jina litakaloonekana kwenye homepage'))
    tagline = models.CharField(max_length=300, blank=True)
    logo = models.ImageField(upload_to='homepage/logos/', blank=True, null=True)

    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_address = models.CharField(max_length=255, blank=True)

    social_facebook = models.URLField(blank=True)
    social_instagram = models.URLField(blank=True)
    social_twitter = models.URLField(blank=True)
    social_whatsapp = models.CharField(max_length=30, blank=True)

    primary_color = models.CharField(max_length=20, default='#6d28d9')
    secondary_color = models.CharField(max_length=20, default='#1f2937')

    is_published = models.BooleanField(
        default=True,
        help_text=_('Ukizima, homepage haionekani tena kwa umma (bado unaweza kuihariri)')
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['content_type', 'object_id'],
                name='unique_homepage_per_owner',
            )
        ]
        verbose_name = _('Home Page')
        verbose_name_plural = _('Home Pages')

    def __str__(self):
        return self.name

    def clean(self):
        if self.content_type_id and self.content_type.model not in ALLOWED_OWNER_MODELS:
            raise ValidationError(_('HomePage inaweza kuunganishwa na Institution au Business pekee.'))

    def is_owned_by(self, user) -> bool:
        owner = self.owner
        return bool(owner and getattr(owner, 'owner_id', None) and owner.owner_id == getattr(user, 'id', None))

    @classmethod
    def get_or_create_for(cls, instance, **defaults):
        """Pata (au tengeneza) HomePage ya Institution/Business fulani."""
        content_type = ContentType.objects.get_for_model(instance)
        if content_type.model not in ALLOWED_OWNER_MODELS:
            raise ValidationError(_('Owner huyu haruhusiwi kuwa na HomePage.'))
        defaults.setdefault('name', getattr(instance, 'name', str(instance)))
        homepage, _created = cls.objects.get_or_create(
            content_type=content_type, object_id=instance.pk, defaults=defaults
        )
        return homepage
