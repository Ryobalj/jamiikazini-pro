# logistics/services/standalone_escrow_release.py

from django.db import transaction as db_transaction


def release_standalone_escrow_if_ready(assignment):
    """
    Achilia fedha za huduma ya usafiri ya moja kwa moja (standalone - ombi
    halihusiani na Order ya bidhaa). Dereva anapokea bei iliyokubaliwa
    (agreed_fare) kutoka kwenye held_balance ya mwombaji. Huitwa na
    escrow_release.release_escrow_if_ready() pale transport_request.order ni
    None - kama transport_request.requested_by pia ni None (ombi la
    business/institution lililoundwa moja kwa moja, si kupitia checkout),
    hakuna kilichoshikiliwa hapo awali, kwa hivyo hakuna cha kuachilia.
    """
    transport_request = assignment.transport_request
    if transport_request.requested_by_id is None:
        return

    from jamiiwallet.models.transaction import Transaction as WalletTransaction
    from jamiiwallet.services.transaction_engine import TransactionEngine

    with db_transaction.atomic():
        requester = transport_request.requested_by
        fare = assignment.agreed_fare or transport_request.estimated_fare
        if fare and fare > 0:
            capture_txn = TransactionEngine.initiate(
                wallet=requester.wallet,
                amount=fare,
                transaction_type=WalletTransaction.TransactionType.CAPTURE,
                initiated_by=requester,
                counterparty=assignment.assigned_to.user,
                metadata={"transport_request_id": str(transport_request.id), "purpose": "standalone_delivery"},
            )
            TransactionEngine.process(capture_txn)
        assignment.update_status(assignment.STATUS_COMPLETED)
