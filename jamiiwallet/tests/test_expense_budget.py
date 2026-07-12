# jamiiwallet/tests/test_expense_budget.py

import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from payments.models.currency import Currency
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.models.expense import Expense
from jamiiwallet.models.budget import Budget, BudgetPeriod
from jamiiwallet.models.transaction import Transaction

User = get_user_model()


@pytest.fixture
def currency(db):
    return Currency.objects.get_or_create(code="TZS")[0]


@pytest.fixture
def user_with_wallet(db, currency):
    user = User.objects.create_user(email="acc@example.com", password="testpass", full_name="Acc User")
    Wallet.objects.update_or_create(user=user, defaults={"balance": Decimal("0.00"), "currency": currency})
    return user


@pytest.mark.django_db
def test_create_expense(user_with_wallet):
    client = APIClient()
    client.force_authenticate(user=user_with_wallet)

    response = client.post(
        reverse('wallet:expense-list'),
        {"amount": "50.00", "category": "FOOD", "note": "chakula cha mchana"},
        format='json',
    )

    assert response.status_code == 201, response.content
    assert Expense.objects.filter(wallet__user=user_with_wallet).count() == 1


@pytest.mark.django_db
def test_expenses_scoped_to_own_wallet(user_with_wallet, currency):
    other = User.objects.create_user(email="other2@example.com", password="testpass")
    Wallet.objects.update_or_create(user=other, defaults={"balance": Decimal("0"), "currency": currency})

    Expense.objects.create(wallet=user_with_wallet.wallet, amount=Decimal("10"), category="FOOD")
    Expense.objects.create(wallet=other.wallet, amount=Decimal("999"), category="FOOD")

    client = APIClient()
    client.force_authenticate(user=user_with_wallet)
    response = client.get(reverse('wallet:expense-list'))

    body = response.json()
    results = body.get("results", body) if isinstance(body, dict) else body
    assert len(results) == 1
    assert Decimal(str(results[0]["amount"])) == Decimal("10")


@pytest.mark.django_db
def test_budget_tracks_spent_and_remaining(user_with_wallet):
    wallet = user_with_wallet.wallet
    budget = Budget.objects.create(
        wallet=wallet, category="FOOD", period=BudgetPeriod.MONTHLY, amount=Decimal("100.00")
    )
    Expense.objects.create(wallet=wallet, amount=Decimal("30"), category="FOOD")
    Expense.objects.create(wallet=wallet, amount=Decimal("20"), category="TRANSPORT")  # tofauti category

    assert budget.spent_amount() == Decimal("30")
    assert budget.remaining_amount == Decimal("70.00")
    assert budget.is_over_budget is False

    Expense.objects.create(wallet=wallet, amount=Decimal("80"), category="FOOD")
    assert budget.is_over_budget is True


@pytest.mark.django_db
def test_wallet_summary_view(user_with_wallet):
    wallet = user_with_wallet.wallet
    wallet.balance = Decimal("500")
    wallet.save()

    Transaction.objects.create(
        wallet=wallet,
        initiated_by=user_with_wallet,
        transaction_type=Transaction.TransactionType.TOP_UP,
        status=Transaction.TransactionStatus.COMPLETED,
        amount=Decimal("500.00"),
    )
    Expense.objects.create(wallet=wallet, amount=Decimal("120.00"), category="RENT")

    client = APIClient()
    client.force_authenticate(user=user_with_wallet)
    response = client.get(reverse('wallet:wallet-summary'))

    assert response.status_code == 200, response.content
    data = response.json()
    assert Decimal(str(data["total_income"])) == Decimal("500.00")
    assert Decimal(str(data["total_expense"])) == Decimal("120.00")
    assert Decimal(str(data["net"])) == Decimal("380.00")
