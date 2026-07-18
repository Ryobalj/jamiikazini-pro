# payments/serializers/paymentmethod_serializer.py

import re
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from payments.models.paymentmethod import (
    PaymentMethod,
    PaymentMethodType,
    MNOType,
    CountryCode,
    RAW_PAN_PATTERN,
    GATEWAY_TOKEN_PREFIXES,
)
from accounts.serializers import UserSerializer  # assuming una serializer ya User

class PaymentMethodSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    method_type_display = serializers.SerializerMethodField()
    mno_display = serializers.SerializerMethodField()
    country_display = serializers.SerializerMethodField()
    last4 = serializers.SerializerMethodField(read_only=True)
    # account_identifier/metadata ni properties (encrypted) - bila hizi DRF angezifanya read-only kimya
    account_identifier = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    metadata = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "owner",
            "method_type",
            "method_type_display",
            "mno",
            "mno_display",
            "country_code",
            "country_display",
            "phone",
            "account_identifier",
            "last4",
            "metadata",
            "details",  # ✅ ongeza field hii
            "is_default",
            "created",
            "updated",
        ]
        read_only_fields = ["created", "updated", "owner"]

    def get_method_type_display(self, obj):
        return obj.get_method_type_display()

    def get_mno_display(self, obj):
        return obj.get_mno_display() if obj.mno else None

    def get_country_display(self, obj):
        return obj.get_country_code_display() if obj.country_code else None

    def get_last4(self, obj):
        # PCI-DSS: kamwe tusidecrypt/kata account_identifier hapa - last4 inatoka
        # kwenye details (iliyowekwa na gateway tokenization response), si kwenye PAN.
        if obj.method_type != PaymentMethodType.CREDIT_CARD:
            return None
        return (obj.details or {}).get("last4")

    def validate_phone(self, value):
        if value:
            country = (self.initial_data.get("country_code") or CountryCode.TZ) if hasattr(self, "initial_data") else CountryCode.TZ
            try:
                PaymentMethod.validate_eac_phone(str(value), country)
            except DjangoValidationError as e:
                raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        method_type = attrs.get("method_type")
        account_id = attrs.get("account_identifier")

        if method_type in [PaymentMethodType.WALLET, PaymentMethodType.CREDIT_CARD] and not account_id:
            raise serializers.ValidationError(
                {"account_identifier": _("Haitakiwi kuwa tupu kwa Wallet au Credit Card")}
            )

        if method_type == PaymentMethodType.CREDIT_CARD and account_id:
            if RAW_PAN_PATTERN.match(account_id):
                raise serializers.ValidationError(
                    {"account_identifier": _(
                        "Haturuhusiwi kutuma namba halisi ya kadi (PAN) moja kwa moja kwa seva. "
                        "Tumia gateway token inayotolewa na Stripe/Flutterwave baada ya "
                        "tokenization salama upande wa client."
                    )}
                )
            if not account_id.startswith(GATEWAY_TOKEN_PREFIXES):
                raise serializers.ValidationError(
                    {"account_identifier": _("account_identifier ya CREDIT_CARD lazima iwe gateway token halali.")}
                )
        return attrs

class PaymentMethodSummarySerializer(serializers.ModelSerializer):
    method_type_display = serializers.SerializerMethodField()
    mno_display = serializers.SerializerMethodField()
    last4 = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "method_type",
            "method_type_display",
            "mno_display",
            "last4",
        ]

    def get_method_type_display(self, obj):
        return obj.get_method_type_display()

    def get_mno_display(self, obj):
        return obj.get_mno_display() if obj.mno else None

    def get_last4(self, obj):
        if obj.method_type != PaymentMethodType.CREDIT_CARD:
            return None
        return (obj.details or {}).get("last4")
