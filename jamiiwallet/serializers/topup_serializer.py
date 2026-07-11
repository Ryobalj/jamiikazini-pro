# jamiiwallet/serializers/topup_serializer.py

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from jamiiwallet.models.topup import TopUp
from kiini.helpers.validators import validate_eac_phone


# Country codes za Afrika Mashariki. Namba ikianza na mojawapo tayari ina country
# code — hatuongezi tena. Vinginevyo tunadhani ni ya kitaifa (TZ) na kuongeza 255.
EAC_COUNTRY_CODES = ("255", "254", "256", "250", "257", "211", "243")
DEFAULT_COUNTRY_CODE = "255"  # Tanzania (MNO zote za app ni za TZ)


def normalize_msisdn(raw: str) -> str:
    """
    Rekebisha namba ya simu kuwa MSISDN kamili ya kimataifa BILA '+' (umbo la PawaPay).
    Hushughulikia miundo yote:
      '0783456789'      -> '255783456789'  (0 ya national trunk -> country code)
      '783456789'       -> '255783456789'  (kitaifa tupu -> ongeza TZ)
      '+255783456789'   -> '255783456789'  ('+' inaondolewa)
      '255783456789'    -> '255783456789'  (tayari kamili)
      '00255783456789'  -> '255783456789'  (international prefix '00' inaondolewa)
      '254712345678'    -> '254712345678'  (nchi nyingine ya EAC inabaki)
    """
    digits = "".join(ch for ch in str(raw or "") if ch.isdigit())
    if not digits:
        return ""

    # 1) Ondoa international prefix '00' (mfano 00255...)
    if digits.startswith("00"):
        digits = digits[2:]

    # 2) Ondoa '0' ya national trunk (0783... -> 783...)
    if digits.startswith("0"):
        digits = digits[1:]

    # 3) Ikiwa tayari ina country code ya EAC, iache; vinginevyo ongeza TZ (255)
    if any(digits.startswith(cc) for cc in EAC_COUNTRY_CODES):
        return digits
    return DEFAULT_COUNTRY_CODE + digits


class TopUpSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    # channel ni ya lazima kimuundo (bila hii, confirm hukwama "Unknown payment channel '').
    # Default = PAWAPAY (sawa na frontend), kwa hivyo topup haitawahi kuwa na channel tupu.
    channel = serializers.ChoiceField(
        choices=TopUp.TopUpChannel.choices,
        required=False,
        default=TopUp.TopUpChannel.PAWAPAY,
    )
    # mno = ufunguo wa mtandao (tigo/yas/airtel/halotel); hubadilishwa kuwa PawaPay code.
    mno = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    reference = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = TopUp
        fields = ['id', 'amount', 'channel', 'mno', 'phone', 'reference', 'status', 'created_at']
        read_only_fields = ['id', 'reference', 'status', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, data):
        channel = (data.get("channel") or "").lower()
        # PawaPay (mobile money) inahitaji MNO + namba halali ya simu.
        if channel in ("pawapay", "pp"):
            mno = (data.get("mno") or "").lower().strip()
            if not mno:
                raise serializers.ValidationError({"mno": "Chagua mtandao (MNO) kwa malipo ya PawaPay."})
            if mno not in settings.PAWAPAY_PROVIDERS:
                allowed = ", ".join(sorted(settings.PAWAPAY_PROVIDERS))
                raise serializers.ValidationError({"mno": f"Mtandao '{mno}' haujaruhusiwa. Chagua: {allowed}."})

            phone = normalize_msisdn(data.get("phone"))
            if not phone:
                raise serializers.ValidationError({"phone": "Weka namba ya simu."})
            try:
                validate_eac_phone("+" + phone)
            except DjangoValidationError:
                raise serializers.ValidationError({"phone": "Namba ya simu si sahihi (tumia +255...)."})

            data["mno"] = mno
            data["phone"] = phone  # hifadhi MSISDN bila '+' kwa PawaPay
        return data

    def create(self, validated_data):
        # TopUp.save() ndio hupanga foleni confirm_topup_transaction.
        validated_data.setdefault("user", self.context["request"].user)
        mno = (validated_data.pop("mno", "") or "").lower()
        if mno:
            validated_data["provider"] = settings.PAWAPAY_PROVIDERS.get(mno, "")
        return TopUp.objects.create(**validated_data)
