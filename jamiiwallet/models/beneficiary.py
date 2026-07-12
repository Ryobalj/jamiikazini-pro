# jamiiwallet/models/beneficiary.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel

User = settings.AUTH_USER_MODEL


class Beneficiary(UUIDModel, TimeStampedModel):
    """
    Mpokeaji aliyehifadhiwa na mtumiaji kwa ajili ya kutuma pesa haraka baadaye
    (bila kuandika namba/email kila wakati).
    """

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='beneficiaries',
        help_text=_('Mtumiaji aliyehifadhi mpokeaji huyu')
    )

    name = models.CharField(max_length=100, help_text=_('Jina la kumbukumbu, mfano: Mama, Rafiki John'))

    identifier = models.CharField(
        max_length=255,
        help_text=_('Namba ya simu au barua pepe ya mpokeaji')
    )

    linked_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='beneficiary_of',
        help_text=_('User halisi anayelingana na identifier, kama yupo kwenye mfumo')
    )

    is_favorite = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_favorite', 'name']
        verbose_name = _('Beneficiary')
        verbose_name_plural = _('Beneficiaries')
        unique_together = ('owner', 'identifier')

    def __str__(self):
        return f'{self.name} ({self.identifier}) - {self.owner}'

    def clean(self):
        if not self.identifier or not self.identifier.strip():
            raise ValidationError(_('Identifier (simu/email) inahitajika.'))
