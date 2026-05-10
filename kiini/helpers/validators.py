# kiini/helpers/validators.py

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_eac_phone(value):
    allowed_prefixes = (
        '+255',  # Tanzania
        '+254',  # Kenya
        '+256',  # Uganda
        '+250',  # Rwanda
        '+257',  # Burundi
        '+211',  # South Sudan
        '+243',  # DRC
    )
    value_str = str(value).strip()

    if not any(value_str.startswith(prefix) for prefix in allowed_prefixes):
        raise ValidationError(
            _("Namba ya simu inapaswa kuwa ya nchi za Afrika Mashariki."),
            code='invalid_eac_phone'
        )