# payments/services/bulk_payment_service.py

from django.utils import timezone
from django.db import transaction as db_txn
from django.core.exceptions import ValidationError
from payments.models.bulk_payment import BulkPaymentTemplate, BulkPaymentExecution
from payments.services.payment_service import PaymentService
import logging
import uuid

logger = logging.getLogger(__name__)

class BulkPaymentService:
    """
    Service for managing bulk payments with coordination
    """
    
    def __init__(self, payment_service: PaymentService = None):
        self.payment_service = payment_service or PaymentService()
    
    def execute_bulk_payment(self, user, payments_data, template_id=None, idempotency_key=None):
        """
        Execute a bulk payment from template or direct data
        """
        idempotency_key = idempotency_key or str(uuid.uuid4())
        
        try:
            with db_txn.atomic():
                # Create execution record
                execution = BulkPaymentExecution.objects.create(
                    executed_by=user,
                    template_id=template_id,
                    total_payments=len(payments_data),
                    idempotency_key=idempotency_key,
                    status=BulkPaymentExecution.Status.PROCESSING
                )
                
                # Process payments asynchronously (or synchronously for small batches)
                self._process_payments_async(execution, payments_data)
                
                return execution
                
        except Exception as e:
            logger.error(f"Failed to execute bulk payment: {e}")
            raise
    

    def _process_payments_async(self, execution, payments_data):
        """
        Process bulk payments asynchronously in production:
        - For small batches, process inline (sync) for latency-sensitive flows.
        - For larger batches, persist payments_data on execution.metadata and fire Celery task with execution.id only.
        """
        # small batches -> sync (optional)
        if len(payments_data) <= 50:
            self._process_payments_sync(execution, payments_data)
            return
    
        # For larger batches, persist the payload in execution.metadata to avoid sending huge payloads via broker
        meta = execution.metadata or {}
        meta["ad_hoc_payments_data"] = payments_data
        execution.metadata = meta
        execution.save(update_fields=["metadata"])
    
        # Trigger Celery task with only execution id
        from jamiitasks.tasks.payment_tasks import process_bulk_payment_task
        process_bulk_payment_task.delay(execution.id)