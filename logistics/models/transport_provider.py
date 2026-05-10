# logistics/models/transport_provider.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models as geomodels
from kiini.models.base import UUIDModel, TimeStampedModel
from kiini.models.institution import Institution
from accounts.models import User


def approval_letter_upload_path(instance, filename):
    return f'transport_providers/approval_letters/{instance.id}/{filename}'


def profile_image_upload_path(instance, filename):
    return f'transport_providers/profile_images/{instance.id}/{filename}'


class TransportProvider(UUIDModel, TimeStampedModel):
    class ProviderType(models.TextChoices):
        INDIVIDUAL = 'individual', _("Dereva Binafsi")
        COMPANY = 'company', _("Kampuni ya Usafirishaji")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transport_providers'
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='transport_providers',
        null=True,
        blank=True
    )
    provider_type = models.CharField(
        max_length=20,
        choices=ProviderType.choices,
        default=ProviderType.INDIVIDUAL,
        help_text=_("Chagua kama huu ni usafiri binafsi au kampuni.")
    )
    location = geomodels.PointField(
        geography=True,
        null=True,
        blank=True,
        help_text=_("Weka GPS ya eneo la kikundi chako, au andika jina la eneo kama GPS haipatikani.")
    )
    is_approved = models.BooleanField(default=False)
    approval_letter = models.FileField(
        upload_to=approval_letter_upload_path,
        null=True,
        blank=True,
        help_text=_("Pakia barua ya uthibitisho wa umoja wako.")
    )
    profile_image = models.ImageField(
        upload_to=profile_image_upload_path,
        null=True,
        blank=True,
        help_text=_("Pakia picha yako ya utambulisho")
    )

    class Meta:
        verbose_name = _("Transport Provider")
        verbose_name_plural = _("Transport Providers")

    def __str__(self):
        return f"{self.user.full_name} - Transport Provider"

    def clean(self):
        # Lazima approval_letter iwepo kama is_approved ni True
        if self.is_approved and not self.approval_letter:
            raise ValidationError(_("Unapaswa kupakia barua ya uthibitisho kabla ya kuidhinishwa."))

        # Zuia faili kubwa zaidi ya 1.5MB kwa approval_letter
        if self.approval_letter and self.approval_letter.size > 1.5 * 1024 * 1024:
            raise ValidationError(_("Barua ya uthibitisho haipaswi kuzidi 1.5MB."))

        # Zuia picha kubwa zaidi ya 1.5MB kwa profile_image
        if self.profile_image and self.profile_image.size > 1.5 * 1024 * 1024:
            raise ValidationError(_("Picha haipaswi kuzidi 1.5MB."))