# jamiiwallet/serializers/cashout_serializer.py
#
# Cash-out kupitia biashara yoyote iliyothibitishwa (mtumiaji anaenda dukani,
# anapewa fedha taslimu na mmiliki wa biashara, na mfumo unahamisha salio la
# wallet kutoka kwa mtumiaji kwenda kwa mmiliki wa biashara). Hutumia Transfer
# (P2P) kama msingi - hakuna ada kwa sasa.

from decimal import Decimal

from rest_framework import serializers

from businesses.models.business import Business
from jamiiwallet.models.transfer import Transfer
from jamiiwallet.models.wallet import Wallet


class CashOutSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    business_id = serializers.UUIDField(write_only=True)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)
    reference = serializers.CharField(read_only=True)
    business_name = serializers.SerializerMethodField()

    class Meta:
        model = Transfer
        fields = [
            'id', 'amount', 'business_id', 'business_name',
            'note', 'reference', 'status', 'created_at',
        ]
        read_only_fields = ['id', 'reference', 'status', 'created_at', 'business_name']

    def get_business_name(self, obj):
        return obj.recipient.full_name if obj.recipient_id else None

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, data):
        request = self.context.get("request")
        sender = getattr(request, "user", None)

        try:
            business = Business.objects.select_related("owner").get(id=data.get("business_id"))
        except (Business.DoesNotExist, ValueError):
            raise serializers.ValidationError({"business_id": "Biashara haikupatikana."})

        if not business.is_verified:
            raise serializers.ValidationError(
                {"business_id": "Biashara hii bado haijathibitishwa - huwezi kutoa fedha kupitia kwake."}
            )
        if not business.owner_id:
            raise serializers.ValidationError({"business_id": "Biashara hii haina mmiliki aliyesajiliwa."})
        if business.owner_id == sender.id:
            raise serializers.ValidationError({"business_id": "Huwezi kutoa fedha kupitia biashara yako mwenyewe."})

        try:
            wallet = Wallet.objects.get(user=sender)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError({"detail": "Wallet haijapatikana."})

        amount = data.get("amount") or Decimal("0")
        if wallet.available_balance < amount:
            raise serializers.ValidationError({"amount": "Salio halitoshi kwa kiasi hiki."})

        prefix = f"Cash-out via {business.name}"
        data["note"] = f"{prefix}: {data['note']}" if data.get("note") else prefix
        data["recipient"] = business.owner
        return data

    def create(self, validated_data):
        validated_data.pop("business_id", None)
        recipient = validated_data.pop("recipient")
        return Transfer.objects.create(
            sender=self.context["request"].user,
            recipient=recipient,
            **validated_data,
        )
