# homepage/models/faq.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel


class Faq(UUIDModel, TimeStampedModel):
    """Swali linaloulizwa mara kwa mara."""

    homepage = models.ForeignKey('homepage.HomePage', on_delete=models.CASCADE, related_name='faqs')

    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')

    def __str__(self):
        return self.question[:100]
