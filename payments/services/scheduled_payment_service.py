# payments/services/scheduled_payment_service.py

from django.utils import timezone
from django.db import transaction as db_txn
from django.core.exceptions import ValidationError
from payments.models.scheduled_payment import ScheduledPayment
from payments.services.payment_service import PaymentService
import logging

logger = logging.getLogger(__name__)

class ScheduledPaymentService:
    """
    Service for managing scheduled payments with coordination
    """
    
    def __init__(self, payment_service: PaymentService = None):
        self.payment_service = payment_service or PaymentService()
    
    def create_scheduled_payment(self, user, amount, currency, payment_method, 
                               recipient_user, schedule_date, description="", metadata=None):
        """
        Create a new scheduled payment with validation
        """
        try:
            with db_txn.atomic():
                # Validate inputs
                if schedule_date <= timezone.now():
                    raise ValidationError("Schedule date must be in the future")
                
                if user == recipient_user:
                    raise ValidationError("Cannot schedule payment to yourself")
                
                # Create scheduled payment
                scheduled_payment = ScheduledPayment.objects.create(
                    created_by=user,
                    amount=amount,
                    currency=currency,
                    payment_method=payment_method,
                    recipient_user=recipient_user,
                    schedule_date=schedule_date,
                    description=description,
                    metadata=metadata or {}
                )
                
                logger.info(f"Scheduled payment created: {scheduled_payment.id}")
                return scheduled_payment
                
        except Exception as e:
            logger.error(f"Failed to create scheduled payment: {e}")
            raise
    
    def execute_due_payments(self):
        """
        Execute all due scheduled payments with proper error handling
        """
        due_payments = ScheduledPayment.objects.filter(
            status=ScheduledPayment.Status.SCHEDULED,
            schedule_date__lte=timezone.now()
        ).select_related('payment_method', 'currency', 'created_by', 'recipient_user')
        
        results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for payment in due_payments:
            try:
                with db_txn.atomic():
                    payment.mark_processing()
                    
                    # Use main PaymentService to process the payment
                    result = self.payment_service.process_payment(
                        user=payment.created_by,
                        amount=payment.amount,
                        payment_method=payment.payment_method,
                        recipient_user=payment.recipient_user,
                        metadata={
                            **payment.metadata,
                            'scheduled_payment_id': str(payment.id),
                            'schedule_date': payment.schedule_date.isoformat()
                        }
                    )
                    
                    if result.get('status') == 'COMPLETED':
                        payment.mark_completed(result.get('tx'))
                        results['successful'] += 1
                        logger.info(f"Scheduled payment {payment.id} completed successfully")
                    else:
                        payment.mark_failed("Payment processing returned non-completed status")
                        results['failed'] += 1
                        results['errors'].append(f"Payment {payment.id}: Processing failed")
                        
            except Exception as e:
                payment.mark_failed(str(e))
                results['failed'] += 1
                results['errors'].append(f"Payment {payment.id}: {e}")
                logger.error(f"Failed to execute scheduled payment {payment.id}: {e}")
            
            results['total_processed'] += 1
        
        return results
    
    def cancel_scheduled_payment(self, payment_id, user):
        """
        Cancel a scheduled payment if it hasn't been processed yet
        """
        try:
            with db_txn.atomic():
                payment = ScheduledPayment.objects.select_for_update().get(
                    id=payment_id,
                    created_by=user
                )
                
                if not payment.can_be_cancelled:
                    raise ValidationError("Cannot cancel payment that is already processing or completed")
                
                payment.cancel()
                logger.info(f"Scheduled payment {payment_id} cancelled by user {user.id}")
                return payment
                
        except ScheduledPayment.DoesNotExist:
            raise ValidationError("Scheduled payment not found")
        except Exception as e:
            logger.error(f"Failed to cancel scheduled payment {payment_id}: {e}")
            raise