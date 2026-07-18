# savings/services/group_wallet_service.py
#
# GroupWallet SI counterparty ya Transaction (angalia maelezo kwenye
# savings/models/group_wallet.py kwa sababu kamili). Fedha zinavuka kati ya
# Wallet ya kibinafsi na GroupWallet kwa hatua MBILI zilizofungwa kwenye
# atomic block moja: (1) mwendo wa kawaida wa TransactionEngine (WITHDRAWAL
# wakati fedha zinaingia kwenye mfuko, TOP_UP wakati zinatoka), na (2)
# sasisho la moja kwa moja, lililofungwa (select_for_update) la
# GroupWallet.balance. TransactionEngine/Transaction haziguswi kabisa.

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction

from savings.models.group_wallet import GroupWallet
from savings.models.contribution import Contribution
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.services.transaction_engine import TransactionEngine


@db_transaction.atomic
def contribute(group, member, amount, idempotency_key=None) -> Contribution:
    if amount <= 0:
        raise DjangoValidationError("Kiasi cha mchango lazima kiwe zaidi ya sifuri.")
    if not hasattr(member, "wallet"):
        raise DjangoValidationError("Wallet ya mwanachama haipatikani.")

    txn = TransactionEngine.initiate(
        wallet=member.wallet,
        amount=amount,
        transaction_type=Transaction.TransactionType.WITHDRAWAL,
        initiated_by=member,
        idempotency_key=idempotency_key,
        metadata={"group_id": str(group.id), "purpose": "group_contribution"},
    )
    if txn.status == Transaction.TransactionStatus.PENDING:
        TransactionEngine.process(txn)

    gw = GroupWallet.objects.select_for_update().get(group=group)
    gw.balance += Decimal(str(amount))
    gw.save(update_fields=["balance", "updated_at"])

    contribution, _created = Contribution.objects.get_or_create(
        source_transaction=txn,
        defaults={"group": group, "member": member, "amount": amount},
    )
    return contribution


@db_transaction.atomic
def execute_withdrawal(withdrawal_request, idempotency_key=None) -> Transaction:
    gw = GroupWallet.objects.select_for_update().get(group=withdrawal_request.group)
    if gw.balance < withdrawal_request.amount:
        raise DjangoValidationError("Salio la mfuko wa kikundi halitoshi kutekeleza ombi hili.")

    recipient = withdrawal_request.requested_by
    if not hasattr(recipient, "wallet"):
        raise DjangoValidationError("Wallet ya mwombaji haipatikani.")

    gw.balance -= withdrawal_request.amount
    gw.save(update_fields=["balance", "updated_at"])

    txn = TransactionEngine.initiate(
        wallet=recipient.wallet,
        amount=withdrawal_request.amount,
        transaction_type=Transaction.TransactionType.TOP_UP,
        initiated_by=recipient,
        idempotency_key=idempotency_key,
        metadata={"group_id": str(withdrawal_request.group_id), "purpose": "group_withdrawal"},
    )
    if txn.status == Transaction.TransactionStatus.PENDING:
        TransactionEngine.process(txn)

    return txn
