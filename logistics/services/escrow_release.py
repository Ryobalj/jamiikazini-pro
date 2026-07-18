# logistics/services/escrow_release.py

from django.db import transaction as db_transaction


def release_escrow_if_ready(assignment):
    """
    Achilia fedha zilizoshikiliwa (escrow) za order husika ikiwa masharti yote
    mawili yametimia: dereva ameweka alama amefikisha (DELIVERED) NA mnunuzi
    amethibitisha amepokea (client_confirmed_at). Muuzaji anapokea kiasi cha
    bidhaa, dereva anapokea kiasi cha usafiri - vyote kutoka kwenye held_balance
    moja ya mnunuzi. Kazi hii ni salama kuitwa mara nyingi (idempotent) kwa
    sababu inaangalia order.payment_status kabla ya kufanya chochote.
    """
    if assignment.assignment_status != assignment.STATUS_DELIVERED:
        return
    if assignment.client_confirmed_at is None:
        return

    transport_request = assignment.transport_request
    order = transport_request.order
    if order is None:
        from logistics.services.standalone_escrow_release import release_standalone_escrow_if_ready
        release_standalone_escrow_if_ready(assignment)
        return

    from businesses.models.order import Order, OrderStatus, PaymentStatus
    from jamiiwallet.models.transaction import Transaction as WalletTransaction
    from jamiiwallet.services.transaction_engine import TransactionEngine

    with db_transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.payment_status != PaymentStatus.HELD:
            return  # tayari imeachiliwa - usifanye tena

        product_amount = order.total_amount - order.delivery_fee
        if product_amount > 0:
            capture_seller = TransactionEngine.initiate(
                wallet=order.client.wallet,
                amount=product_amount,
                transaction_type=WalletTransaction.TransactionType.CAPTURE,
                initiated_by=order.client,
                counterparty=order.business.owner,
                metadata={"order_id": str(order.id), "purpose": "product"},
            )
            TransactionEngine.process(capture_seller)

        driver_amount = assignment.agreed_fare or order.delivery_fee
        if driver_amount and driver_amount > 0:
            capture_driver = TransactionEngine.initiate(
                wallet=order.client.wallet,
                amount=driver_amount,
                transaction_type=WalletTransaction.TransactionType.CAPTURE,
                initiated_by=order.client,
                counterparty=assignment.assigned_to.user,
                metadata={"order_id": str(order.id), "purpose": "delivery"},
            )
            TransactionEngine.process(capture_driver)

        order.payment_status = PaymentStatus.PAID
        order.status = OrderStatus.COMPLETED
        order.save(update_fields=["payment_status", "status"])

        assignment.update_status(assignment.STATUS_COMPLETED)
