# jamiiwallet/serializers/transfer_serializer.py

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from accounts.models import User
from jamiiwallet.models.transfer import Transfer
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.serializers.topup_serializer import normalize_msisdn
from kiini.helpers.validators import validate_eac_phone


def find_recipient(identifier: str) -> User | None:
    """Tafuta User kwa email (indexed) au namba ya simu (phone_number ni encrypted,
    hivyo hufanya scan - inafanana na mtindo unaotumika transaction_preprocessor.py)."""
    identifier = (identifier or "").strip()
    if not identifier:
        return None
    if "@" in identifier:
        return User.objects.filter(email__iexact=identifier).first()

    phone = normalize_msisdn(identifier)
    if not phone:
        return None
    try:
        validate_eac_phone("+" + phone)
    except DjangoValidationError:
        return None
    target = "+" + phone
    return next((u for u in User.objects.all() if u.phone_number == target), None)


class TransferSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    recipient_identifier = serializers.CharField(write_only=True)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)
    reference = serializers.CharField(read_only=True)
    recipient_name = serializers.SerializerMethodField()

    class Meta:
        model = Transfer
        fields = [
            'id', 'amount', 'recipient_identifier', 'recipient_name',
            'note', 'reference', 'status', 'created_at',
        ]
        read_only_fields = ['id', 'reference', 'status', 'created_at', 'recipient_name']

    def get_recipient_name(self, obj):
        return obj.recipient.full_name if obj.recipient_id else None

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, data):
        request = self.context.get("request")
        sender = getattr(request, "user", None)

        recipient = find_recipient(data.get("recipient_identifier"))
        if not recipient:
            raise serializers.ValidationError({"recipient_identifier": "Mpokeaji hakupatikana."})
        if recipient.id == sender.id:
            raise serializers.ValidationError({"recipient_identifier": "Huwezi kujitumia pesa mwenyewe."})

        try:
            wallet = Wallet.objects.get(user=sender)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError({"detail": "Wallet haijapatikana."})

        amount = data.get("amount") or Decimal("0")
        if wallet.available_balance < amount:
            raise serializers.ValidationError({"amount": "Salio halitoshi kwa kiasi hiki."})

        data["recipient"] = recipient
        return data

    def create(self, validated_data):
        validated_data.pop("recipient_identifier", None)
        recipient = validated_data.pop("recipient")
        return Transfer.objects.create(
            sender=self.context["request"].user,
            recipient=recipient,
            **validated_data,
        )
