# payments/models/paymentmethod.py

import re
import json
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import models
from kiini.models.base_entity import AbstractEntity
from security.helpers.encryption import encrypt_data, decrypt_data
from payments.gateways.flutterwave.client import FlutterwaveGateway
from payments.gateways.stripe.client import StripeGateway
from payments.models.currency import Currency


# -----------------
# Prefixes & Regex
# -----------------
EAC_PREFIXES = {
    "TZ": {"621", "622", "625", "626", "627", "628", "629", "651", "652", "653", "654",
           "655", "656", "657", "658", "659", "661", "662", "663", "664", "665", "666",
           "667", "668", "669", "671", "672", "673", "674", "675", "676", "677", "678",
           "679", "681", "682", "683", "684", "685", "686", "687", "688", "689", "691",
           "692", "693", "694", "695", "696", "697", "698", "699", "711", "712", "713",
           "714", "715", "716", "717", "718", "719", "731", "732", "733", "734", "735",
           "736", "737", "738", "739", "741", "742", "743", "744", "745", "746", "747",
           "748", "749", "751", "752", "753", "754", "755", "756", "757", "758", "759",
           "761", "762", "763", "764", "765", "766", "767", "768", "769", "771", "772",
           "773", "774", "775", "776", "777", "778", "779", "781", "782", "783", "784",
           "785", "786", "787", "788", "789"},
    "KE": {"700", "701", "702", "703", "704", "705", "706", "707", "708", "709",
           "710", "711", "712", "713", "714", "715", "716", "717", "718", "719",
           "720", "721", "722", "723", "724", "725", "726", "727", "728", "729",
           "740", "741", "742", "743", "745", "746", "748", "749", "750", "751",
           "752", "753", "754", "755", "756", "757", "758", "759", "769", "770",
           "771", "772", "773", "774", "775", "776", "777", "778", "779", "780",
           "781", "782", "783", "784", "785", "786", "787", "788", "789", "790",
           "791", "792", "793", "794", "795", "796", "797", "798", "799"},
    "UG": {"70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "39", "41", "31"},
    "RW": {"72", "73", "74", "75", "76", "78", "79"},
    "BI": {"61", "62", "69", "71", "72", "75", "76", "79"},
    "SS": {"91", "92", "95", "97", "98", "99"},
}

EAC_REGEX = {
    "TZ": r"^\+255\d{9}$",
    "KE": r"^\+254\d{9}$",
    "UG": r"^\+256\d{9}$",
    "RW": r"^\+250\d{9}$",
    "BI": r"^\+257\d{8}$",
    "SS": r"^\+211\d{8}$",
}


# -----------------
# Choices
# -----------------
class PaymentMethodType(models.TextChoices):
    WALLET = "WALLET", _("Wallet")
    CREDIT_CARD = "CREDIT_CARD", _("Credit Card")
    PAWAPAY = "PAWAPAY", _("PawaPay (MNO Gateway)")


class MNOType(models.TextChoices):
    VODACOM = "VODACOM", _("Vodacom M-Pesa")
    AIRTEL = "AIRTEL", _("Airtel Money")
    YAS = "YAS", _("YAS (MixByYAS)")
    HALOTEL = "HALOTEL", _("HaloPesa")
    ZANTEL = "ZANTEL", _("EzyPesa")
    MTN = "MTN", _("MTN Mobile Money")
    SAFARICOM = "SAFARICOM", _("M-Pesa Kenya")
    TELKOM_KE = "TELKOM_KE", _("T-Kash")
    AFRICELL = "AFRICELL", _("Africell Money")
    EQUITEL = "EQUITEL", _("Equitel Money")
    OTHER = "OTHER", _("Other")
    MIXBYYAS = "MIXBYYAS", _("MixByYAS")  # alias reference


MNO_ALIASES = {
    "TIGO": "YAS",
    "TIGOPESA": "MIXBYYAS"
}

# PCI-DSS: CREDIT_CARD account_identifier lazima iwe gateway token (Stripe/Flutterwave),
# kamwe si namba halisi ya kadi (PAN). Prefixes hizi ndizo pekee zinazokubalika.
GATEWAY_TOKEN_PREFIXES = ("pm_", "tok_", "card_", "flw_", "src_")
RAW_PAN_PATTERN = re.compile(r"^\d{12,19}$")


class GatewayType(models.TextChoices):
    PAWAPAY = "PAWAPAY", _("PawaPay")
    STRIPE = "STRIPE", _("Stripe")
    FLUTTERWAVE = "FLUTTERWAVE", _("Flutterwave")


class CountryCode(models.TextChoices):
    TZ = "TZ", _("Tanzania")
    KE = "KE", _("Kenya")
    UG = "UG", _("Uganda")
    RW = "RW", _("Rwanda")
    BI = "BI", _("Burundi")
    SS = "SS", _("South Sudan")


# -----------------
# PaymentMethod Model
# -----------------
class PaymentMethod(AbstractEntity):
    method_type = models.CharField(max_length=20, choices=PaymentMethodType.choices)
    mno = models.CharField(max_length=20, choices=MNOType.choices, blank=True, null=True)
    country_code = models.CharField(max_length=2, choices=CountryCode.choices, default=CountryCode.TZ)
    gateway = models.CharField(max_length=20, choices=GatewayType.choices, blank=True, null=True)
    # TextField: thamani huhifadhiwa ikiwa encrypted (Fernet token > 100 chars kwa identifier ndefu)
    _account_identifier = models.TextField(blank=True, null=True, db_column="account_identifier")
    currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Currency associated with this payment method",
    )
    _metadata = models.JSONField(blank=True, null=True, db_column="metadata")
    details = models.JSONField(default=dict, blank=True)  # ✅ fixed (was lambda: {})
    is_default = models.BooleanField(default=False)

    # ---------- Account Identifier ----------
    @property
    def account_identifier(self):
        if not self._account_identifier:
            return None
        try:
            return decrypt_data(self._account_identifier)
        except Exception:
            return "[DECRYPTION FAILED]"

    @account_identifier.setter
    def account_identifier(self, value):
        self._account_identifier = encrypt_data(value) if value else None

    # ---------- Metadata ----------
    @property
    def metadata(self):
        if not self._metadata:
            return None
        try:
            decrypted = decrypt_data(self._metadata)
            return json.loads(decrypted)
        except Exception:
            return {}

    @metadata.setter
    def metadata(self, value):
        self._metadata = encrypt_data(json.dumps(value)) if value else None

    # ---------- Gateway helpers ----------
    @property
    def is_stripe(self):
        return self.method_type == PaymentMethodType.CREDIT_CARD and self.gateway == GatewayType.STRIPE

    @property
    def is_flutterwave(self):
        return self.method_type == PaymentMethodType.CREDIT_CARD and self.gateway == GatewayType.FLUTTERWAVE

    def get_payment_client(self):
        if self.is_stripe:
            return StripeGateway()
        if self.is_flutterwave:
            return FlutterwaveGateway()
        return None

    # ---------- EAC Phone Validation ----------
    @staticmethod
    def validate_eac_phone(phone, country_code="TZ"):
        """Thibitisha namba ya simu ni halali kwa nchi za Afrika Mashariki (EAC)."""
        if not phone:
            return phone
        error = ValidationError(
            _("Namba ya simu si halali kwa nchi za Afrika Mashariki (EAC).")
        )
        pattern = EAC_REGEX.get(country_code)
        if not pattern or not re.match(pattern, phone):
            raise error
        prefixes = EAC_PREFIXES.get(country_code, set())
        national = phone[4:]  # nchi zote za EAC zina country code ya tarakimu 3 (+2XX)
        if prefixes and not any(national.startswith(p) for p in prefixes):
            raise error
        return phone

    def clean(self):
        super().clean()
        if self.phone:
            PaymentMethod.validate_eac_phone(str(self.phone), self.country_code or "TZ")
        self._reject_raw_pan()

    def _reject_raw_pan(self):
        """PCI-DSS: hatuhifadhi namba halisi ya kadi (PAN) kwenye seva zetu kamwe -
        account_identifier ya CREDIT_CARD lazima iwe gateway token (Stripe/Flutterwave)."""
        if self.method_type != PaymentMethodType.CREDIT_CARD:
            return
        identifier = self.account_identifier
        if not identifier:
            return
        if RAW_PAN_PATTERN.match(identifier):
            raise ValidationError(
                _("Haturuhusiwi kuhifadhi namba halisi ya kadi (PAN). Tumia gateway token "
                  "(mf. Stripe/Flutterwave) baada ya tokenization salama upande wa client.")
            )
        if not identifier.startswith(GATEWAY_TOKEN_PREFIXES):
            raise ValidationError(
                _("account_identifier ya CREDIT_CARD lazima iwe gateway token halali.")
            )

    # ---------- Intelligent Account Detection ----------
    def _detect_identifier_type(self, identifier: str):
        if not identifier:
            return "UNKNOWN", "****"

        if re.match(r"^\+\d{10,15}$", identifier):
            return "PHONE", f"****{identifier[-4:]}"
        if identifier.startswith(GATEWAY_TOKEN_PREFIXES):
            return "GATEWAY_TOKEN", identifier[:6] + "..."
        if re.match(r"^[A-Za-z0-9\-]{6,}$", identifier):
            return "WALLET", identifier[:4] + "..." + identifier[-3:]
        return "UNKNOWN", "****"

    # ---------- Save ----------
    def save(self, *args, **kwargs):
        if self.mno in MNO_ALIASES:
            self.mno = MNO_ALIASES[self.mno]

        self._reject_raw_pan()

        if self._account_identifier:
            try:
                identifier = decrypt_data(self._account_identifier)
            except Exception:
                identifier = None

            if identifier:
                detected_type, masked = self._detect_identifier_type(identifier)
                if not self.details:
                    self.details = {}
                self.details["identifier_type"] = detected_type
                self.details["masked_identifier"] = masked

        super().save(*args, **kwargs)

    # ---------- String Representation ----------
    def __str__(self):
        user = self.owner or _("Unknown User")

        if self.method_type == PaymentMethodType.PAWAPAY:
            mno_display = self.get_mno_display() or _("Unknown MNO")
            return _("%(mno)s via PawaPay - %(phone)s") % {
                "mno": mno_display, "phone": getattr(self, "phone", "-")
            }

        if self.method_type == PaymentMethodType.WALLET:
            return _("Wallet (%(id)s) - %(user)s") % {
                "id": self.account_identifier, "user": user
            }

        if self.method_type == PaymentMethodType.CREDIT_CARD:
            gateway_name = self.gateway or _("Unknown Gateway")
            last4 = (self.details or {}).get("last4") or "****"
            return _("Card ending %(last4)s via %(gateway)s - %(user)s") % {
                "last4": last4, "gateway": gateway_name, "user": user
            }

        return _("%(method)s - %(id)s") % {
            "method": self.get_method_type_display(),
            "id": self.account_identifier or _("N/A")
        }

    @property
    def method_type_display(self):
        return self.get_method_type_display()