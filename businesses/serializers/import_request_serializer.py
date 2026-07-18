# businesses/serializers/import_request_serializer.py

from decimal import Decimal
from rest_framework import serializers

from businesses.models.import_request import ImportRequest
from payments.models.currency import Currency


class ImportRequestSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.full_name", read_only=True, default=None)
    budget_currency_code = serializers.CharField(source="budget_currency.code", read_only=True, default=None)
    claimed_by_business_name = serializers.CharField(source="claimed_by_business.name", read_only=True, default=None)

    class Meta:
        model = ImportRequest
        fields = [
            "id", "buyer", "buyer_name", "item_description", "origin_country",
            "quantity", "budget_amount", "budget_currency", "budget_currency_code",
            "status", "claimed_by_business", "claimed_by_business_name",
            "claimed_price", "estimated_lead_days", "claimed_at", "order", "created_at",
        ]
        read_only_fields = fields


class ImportRequestCreateSerializer(serializers.Serializer):
    item_description = serializers.CharField()
    origin_country = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=Decimal("0.001"), default=Decimal("1")
    )
    budget_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0.01"), required=False, allow_null=True
    )
    budget_currency_code = serializers.CharField(max_length=10, required=False, allow_blank=True)

    def create(self, validated_data):
        request = self.context["request"]

        budget_currency = None
        code = (validated_data.get("budget_currency_code") or "").strip().upper()
        if code:
            budget_currency = Currency.objects.filter(code=code).first()

        import_request = ImportRequest.objects.create(
            buyer=request.user,
            item_description=validated_data["item_description"].strip(),
            origin_country=(validated_data.get("origin_country") or "").strip(),
            quantity=validated_data["quantity"],
            budget_amount=validated_data.get("budget_amount"),
            budget_currency=budget_currency,
        )

        self._notify_import_businesses()
        return import_request

    @staticmethod
    def _notify_import_businesses():
        from kiini.helpers.notification_helper import notify_user
        from businesses.models.business import Business

        notified_owners = set()
        importers = Business.objects.filter(
            deals_in_imports=True, is_active=True
        ).select_related("owner")
        for business in importers:
            if business.owner_id in notified_owners:
                continue
            notified_owners.add(business.owner_id)
            notify_user(
                business.owner,
                "Kuna ombi jipya la uagizaji wa bidhaa (import request) kwenye Jamiikazini.",
            )


class ImportRequestClaimSerializer(serializers.Serializer):
    business_id = serializers.UUIDField()
    price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    currency_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    estimated_lead_days = serializers.IntegerField(min_value=1, max_value=365)
