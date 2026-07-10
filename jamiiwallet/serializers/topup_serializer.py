# jamiiwallet/serializers/topup_serializer.py

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from jamiiwallet.models.topup import TopUp
from kiini.helpers.validators import validate_eac_phone


def normalize_msisdn(raw: str) -> str:
    """
    Rekebisha namba ya simu kuwa MSISDN ya kimataifa BILA '+' (umbo la PawaPay),
    mfano '0783456789' / '+255783456789' / '255783456789' -> '255783456789'.
    Default country code = 255 (Tanzania), kwa kuwa MNO ni za TZ.
    """
    digits = "".join(ch for ch in str(raw or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("0"):
        digits = "255" + digits[1:]
    return digits


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
