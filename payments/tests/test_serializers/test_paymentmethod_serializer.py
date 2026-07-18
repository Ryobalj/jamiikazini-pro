# payments/tests/test_serializers/test_paymentmethod_serializer.py

import pytest
from rest_framework.exceptions import ValidationError
from payments.serializers.paymentmethod_serializer import (
    PaymentMethodSerializer,
    PaymentMethodSummarySerializer,
)
from payments.models.paymentmethod import PaymentMethod, PaymentMethodType, MNOType, CountryCode


@pytest.mark.django_db
def test_paymentmethodserializer_serialization(user_factory):
    owner = user_factory()
    pm = PaymentMethod.objects.create(
        owner=owner,
        method_type=PaymentMethodType.WALLET,
        mno=MNOType.VODACOM,
        country_code=CountryCode.TZ,
        phone="+255688123456",
        account_identifier="WALLET-123",
        metadata={"test": "meta"},
    )
    serializer = PaymentMethodSerializer(pm)

    data = serializer.data
    assert data["id"] == str(pm.id)
    assert data["owner"]["id"] == str(owner.id)
    assert data["method_type_display"] == pm.get_method_type_display()
    assert data["mno_display"] == pm.get_mno_display()
    assert data["country_display"] == pm.get_country_code_display()
    assert data["last4"] is None  # wallet sio credit card
    assert data["metadata"] == {"test": "meta"}


@pytest.mark.django_db
def test_get_last4_credit_card(user_factory):
    owner = user_factory()
    # PCI-DSS: account_identifier ni gateway token, si PAN. last4 inatoka details
    # (iliyotolewa na gateway tokenization response), si kwa kukata identifier.
    pm = PaymentMethod.objects.create(
        owner=owner,
        method_type=PaymentMethodType.CREDIT_CARD,
        mno=MNOType.AIRTEL,
        country_code=CountryCode.KE,
        phone="+254701234567",
        account_identifier="pm_1111111111111111",
        details={"last4": "1111", "brand": "visa"},
    )
    serializer = PaymentMethodSerializer(pm)
    assert serializer.data["last4"] == "1111"

    # Summary serializer pia
    summary = PaymentMethodSummarySerializer(pm)
    assert summary.data["last4"] == "1111"


@pytest.mark.django_db
def test_get_last4_credit_card_without_account(user_factory):
    owner = user_factory()
    pm = PaymentMethod.objects.create(
        owner=owner,
        method_type=PaymentMethodType.CREDIT_CARD,
        mno=MNOType.YAS,
        country_code=CountryCode.RW,
        phone="+250788123456",
        account_identifier="",
    )
    serializer = PaymentMethodSerializer(pm)
    assert serializer.data["last4"] is None

    summary = PaymentMethodSummarySerializer(pm)
    assert summary.data["last4"] is None


def test_validate_phone_calls_model_validator(mocker, user_factory):
    from payments.serializers.paymentmethod_serializer import PaymentMethodSerializer

    mock_validator = mocker.patch(
        "payments.models.paymentmethod.PaymentMethod.validate_eac_phone"
    )

    user = user_factory()
    data = {
        "owner": user.id,
        "phone": "+255688000111",
        "country_code": "TZ",
        "method_type": "CREDIT_CARD",
        "account_identifier": "pm_1234",
    }

    serializer = PaymentMethodSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    # Hakuna wito wa ziada la validate_phone
    mock_validator.assert_called_once_with(data["phone"], "TZ")


def test_validate_requires_account_identifier_for_wallet():
    serializer = PaymentMethodSerializer()
    attrs = {"method_type": PaymentMethodType.WALLET, "account_identifier": ""}
    with pytest.raises(ValidationError) as exc:
        serializer.validate(attrs)
    assert "account_identifier" in str(exc.value)


def test_validate_requires_account_identifier_for_credit_card():
    serializer = PaymentMethodSerializer()
    attrs = {"method_type": PaymentMethodType.CREDIT_CARD, "account_identifier": None}
    with pytest.raises(ValidationError) as exc:
        serializer.validate(attrs)
    assert "account_identifier" in str(exc.value)


def test_validate_ok_for_other_methods():
    serializer = PaymentMethodSerializer()
    # Tumia account_identifier sahihi (gateway token) ili isishindwe na validation
    attrs = {"method_type": PaymentMethodType.CREDIT_CARD, "account_identifier": "pm_1234"}
    validated = serializer.validate(attrs)
    assert validated["account_identifier"] == "pm_1234"


def test_validate_rejects_raw_pan_for_credit_card():
    serializer = PaymentMethodSerializer()
    attrs = {"method_type": PaymentMethodType.CREDIT_CARD, "account_identifier": "4111111111111111"}
    with pytest.raises(ValidationError) as exc:
        serializer.validate(attrs)
    assert "account_identifier" in str(exc.value)


def test_validate_rejects_non_token_identifier_for_credit_card():
    serializer = PaymentMethodSerializer()
    attrs = {"method_type": PaymentMethodType.CREDIT_CARD, "account_identifier": "not-a-gateway-token"}
    with pytest.raises(ValidationError) as exc:
        serializer.validate(attrs)
    assert "account_identifier" in str(exc.value)
