# kiini/models/base_entity.py

from django.db import models
from django.contrib.gis.db import models as geomodels
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from .base import UUIDModel, TimeStampedModel
from kiini.helpers.validators import validate_eac_phone

from django.contrib.auth import get_user_model
User = get_user_model()


class AbstractEntity(UUIDModel, TimeStampedModel):
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_owner",
        verbose_name=_("Owner")
    )

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))

    phone = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_("Phone"),
        help_text=_("Namba ya simu ya kimataifa (Mfano: +255...)."),
        validators=[validate_eac_phone],
    )

    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name=_("Phone Verified"),
        help_text=_("Je namba hii ya simu imethibitishwa kwa SMS?")
    )

    location = geomodels.PointField(geography=True, null=True, blank=True, verbose_name=_("Location"))
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Address"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        abstract = True