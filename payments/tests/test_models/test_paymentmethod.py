# payments/tests/test_models/test_paymentmethod.py

import pytest
from django.core.exceptions import ValidationError
from payments.models.paymentmethod import (
    PaymentMethod,
    PaymentMethodType,
    MNOType,
    MNO_ALIASES,
    CountryCode,
)

@pytest.mark.django_db
class TestPaymentMethodModel:

    def test_str_pawapay_with_mno_and_phone(self, user_factory):
        pm = PaymentMethod.objects.create(
            owner=user_factory(),
            method_type=PaymentMethodType.PAWAPAY,
            mno=MNOType.VODACOM,
            phone="+255712345678",
        )
        s = str(pm)
        assert "Vodacom" in s
        assert "+255712345678" in s

    def test_str_wallet(self, user_factory):
        user = user_factory(full_name="Juma")
        pm = PaymentMethod.objects.create(
            owner=user,
            method_type=PaymentMethodType.WALLET,
            account_identifier="W123",
        )
        s = str(pm)
        assert "W123" in s
        assert "Juma" in s

    def test_str_credit_card_with_and_without_account_identifier(self, user_factory):
        user = user_factory(full_name="Amina")
        # PCI-DSS: account_identifier ni gateway token, si PAN halisi. last4 inatoka
        # details (kama ingetolewa na gateway tokenization response).
        pm1 = PaymentMethod.objects.create(
            owner=user,
            method_type=PaymentMethodType.CREDIT_CARD,
            account_identifier="pm_1234567812345678",
            details={"last4": "5678", "brand": "visa"},
        )
        assert "5678" in str(pm1)

        pm2 = PaymentMethod.objects.create(
            owner=user,
            method_type=PaymentMethodType.CREDIT_CARD,
            account_identifier=None,
        )
        assert "****" in str(pm2)

    def test_credit_card_rejects_raw_pan(self, user_factory):
        pm = PaymentMethod(
            owner=user_factory(),
            method_type=PaymentMethodType.CREDIT_CARD,
            account_identifier="4242424242424242",
        )
        with pytest.raises(ValidationError):
            pm.save()

    def test_credit_card_rejects_non_gateway_token_identifier(self, user_factory):
        pm = PaymentMethod(
            owner=user_factory(),
            method_type=PaymentMethodType.CREDIT_CARD,
            account_identifier="not-a-real-token",
        )
        with pytest.raises(ValidationError):
            pm.save()

    def test_credit_card_accepts_gateway_token(self, user_factory):
        pm = PaymentMethod.objects.create(
            owner=user_factory(),
            method_type=PaymentMethodType.CREDIT_CARD,
            account_identifier="pm_abcdef123456",
            details={"last4": "4242", "brand": "visa"},
        )
        pm.refresh_from_db()
        assert pm.details["identifier_type"] == "GATEWAY_TOKEN"

    def test_str_default_fallback(self):
        pm = PaymentMethod.objects.create(
            method_type=PaymentMethodType.WALLET,
            account_identifier="ABC123",
            owner=None,
        )
        # Kwa kuwa method_type ni WALLET, itatumia format ya Wallet
        assert "Wallet" in str(pm)

    def test_save_converts_mno_alias(self):
        pm = PaymentMethod.objects.create(
            method_type=PaymentMethodType.PAWAPAY,
            mno="TIGO",
            phone="+255712345678",
        )
        pm.refresh_from_db()
        assert pm.mno == MNO_ALIASES["TIGO"]

    def test_clean_valid_eac_phone(self, user_factory):
        pm = PaymentMethod(
            method_type=PaymentMethodType.WALLET,
            phone="+255688619442",  # TZ valid
        )
        # Should not raise
        pm.clean()

    def test_clean_invalid_eac_phone_raises(self):
        pm = PaymentMethod(
            method_type=PaymentMethodType.WALLET,
            phone="+999123456789",  # not EAC
        )
        with pytest.raises(ValidationError) as excinfo:
            pm.clean()
        assert "Afrika Mashariki" in str(excinfo.value)

    def test_clean_skips_validation_for_valid_eac_phone(self):
        # Namba halali ya EAC (TZ)
        pm = PaymentMethod(
            method_type=PaymentMethodType.WALLET,
            phone="+255688619442",  # TZ valid
        )
        # Hakutakuwa na error
        pm.clean()