# jamiiwallet/serializers/withdrawal_serializer.py

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from jamiiwallet.models.withdrawal import Withdrawal
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.serializers.topup_serializer import normalize_msisdn
from kiini.helpers.validators import validate_eac_phone


class WithdrawalSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    channel = serializers.ChoiceField(
        choices=Withdrawal.WithdrawalChannel.choices,
        required=False,
        default=Withdrawal.WithdrawalChannel.PAWAPAY,
    )
    # mno = ufunguo wa mtandao (tigo/yas/airtel/halotel); hubadilishwa kuwa PawaPay code.
    mno = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    reference = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = Withdrawal
        fields = ['id', 'amount', 'channel', 'mno', 'phone', 'reference', 'status', 'created_at']
        read_only_fields = ['id', 'reference', 'status', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        # Kagua salio la wallet linatosha
        amount = data.get("amount") or Decimal("0")
        try:
            wallet = Wallet.objects.get(user=user)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError({"detail": "Wallet haijapatikana."})
        if wallet.available_balance < amount:
            raise serializers.ValidationError({"amount": "Salio halitoshi kwa kiasi hiki."})

        channel = (data.get("channel") or "").lower()
        if channel in ("pawapay", "pp"):
            mno = (data.get("mno") or "").lower().strip()
            if not mno:
                raise serializers.ValidationError({"mno": "Chagua mtandao (MNO) kwa payout ya PawaPay."})
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
            data["phone"] = phone
        return data

    def create(self, validated_data):
        # Withdrawal.save() ndio hupanga foleni process_withdrawal_transaction.
        validated_data.setdefault("user", self.context["request"].user)
        mno = (validated_data.pop("mno", "") or "").lower()
        if mno:
            validated_data["provider"] = settings.PAWAPAY_PROVIDERS.get(mno, "")
        return Withdrawal.objects.create(**validated_data)
