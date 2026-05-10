# payments/services/payment_link_service.py

from django.utils import timezone
from django.db import transaction as db_txn
from django.core.exceptions import ValidationError
from django.conf import settings
from payments.models.payment_link import PaymentLink
from payments.services.payment_service import PaymentService
import logging
import secrets
import string

logger = logging.getLogger(__name__)

class PaymentLinkService:
    """
    Service for managing payment links
    """
    
    def __init__(self, payment_service: PaymentService = None):
        self.payment_service = payment_service or PaymentService()
    
    def generate_link_code(self, length=16):
        """Generate unique payment link code"""
        alphabet = string.ascii_letters + string.digits
        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(length))
            if not PaymentLink.objects.filter(link_code=code).exists():
                return code
    
    def create_payment_link(self, user, amount, currency, description, 
                          expires_in_days=7, allowed_methods=None, metadata=None):
        """
        Create a new payment link
        """
        try:
            with db_txn.atomic():
                expires_at = timezone.now() + timezone.timedelta(days=expires_in_days)
                link_code = self.generate_link_code()
                
                payment_link = PaymentLink.objects.create(
                    created_by=user,
                    amount=amount,
                    currency=currency,
                    description=description,
                    link_code=link_code,
                    expires_at=expires_at,
                    allowed_methods=allowed_methods or ['WALLET', 'PAWAPAY'],
                    metadata=metadata or {}
                )
                
                logger.info(f"Payment link created: {link_code} by user {user.id}")
                return payment_link
                
        except Exception as e:
            logger.error(f"Failed to create payment link: {e}")
            raise
    
    def process_payment_link(self, link_code, user, payment_method, metadata=None):
        """
        Process payment using a payment link
        """
        try:
            with db_txn.atomic():
                payment_link = PaymentLink.objects.select_for_update().get(
                    link_code=link_code
                )
                
                # Validate link usability
                if not payment_link.is_usable:
                    raise ValidationError("Payment link is not usable")
                
                # Process payment
                result = self.payment_service.process_payment(
                    user=user,
                    amount=payment_link.amount,
                    payment_method=payment_method,
                    recipient_user=payment_link.created_by,
                    metadata={
                        **(metadata or {}),
                        'payment_link_code': link_code,
                        'original_description': payment_link.description
                    }
                )
                
                # Mark link as used
                if result.get('status') == 'COMPLETED':
                    payment_link.mark_as_used(user, result.get('tx'))
                    logger.info(f"Payment link {link_code} used successfully by user {user.id}")
                else:
                    raise ValidationError("Payment processing failed")
                
                return result
                
        except PaymentLink.DoesNotExist:
            raise ValidationError("Payment link not found")
        except Exception as e:
            logger.error(f"Failed to process payment link {link_code}: {e}")
            raise
    
    def get_active_links(self, user):
        """Get active payment links for a user"""
        return PaymentLink.objects.filter(
            created_by=user,
            status=PaymentLink.Status.ACTIVE,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')
    
    def cleanup_expired_links(self):
        """
        Mark expired payment links as expired
        """
        try:
            expired_links = PaymentLink.objects.filter(
                status=PaymentLink.Status.ACTIVE,
                expires_at__lte=timezone.now()
            )
            
            count = expired_links.count()
            
            for link in expired_links:
                link.mark_as_expired()
            
            logger.info(f"Marked {count} payment links as expired")
            return {'expired_count': count}
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired payment links: {e}")
            return {'expired_count': 0, 'error': str(e)}
    
    def extend_payment_link(self, link_code, new_expires_at, user):
        """
        Extend payment link expiry
        """
        try:
            with db_txn.atomic():
                payment_link = PaymentLink.objects.select_for_update().get(
                    link_code=link_code,
                    created_by=user
                )
                
                if payment_link.used_by:
                    raise ValidationError("Cannot extend used payment link")
                
                payment_link.extend_expiry(new_expires_at)
                logger.info(f"Payment link {link_code} extended to {new_expires_at}")
                return payment_link
                
        except PaymentLink.DoesNotExist:
            raise ValidationError("Payment link not found")
        except Exception as e:
            logger.error(f"Failed to extend payment link {link_code}: {e}")
            raise
    
    def get_link_analytics(self, user, days=30):
        """
        Get analytics for user's payment links
        """
        try:
            from django.db.models import Count, Sum, Q
            from django.utils import timezone
            
            start_date = timezone.now() - timezone.timedelta(days=days)
            
            analytics = PaymentLink.objects.filter(
                created_by=user,
                created_at__gte=start_date
            ).aggregate(
                total_links=Count('id'),
                active_links=Count('id', filter=Q(
                    status=PaymentLink.Status.ACTIVE,
                    expires_at__gt=timezone.now()
                )),
                used_links=Count('id', filter=Q(status=PaymentLink.Status.USED)),
                total_amount=Sum('amount', filter=Q(status=PaymentLink.Status.USED)),
                successful_payments=Count('id', filter=Q(
                    status=PaymentLink.Status.USED,
                    used_at__isnull=False
                ))
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get payment link analytics: {e}")
            return {}