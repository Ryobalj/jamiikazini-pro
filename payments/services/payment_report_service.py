# payments/services/payment_report_service.py

from django.utils import timezone
from django.db import transaction as db_txn
from django.db.models import Count, Sum, Avg, Q
from django.core.exceptions import ValidationError
from payments.models.payment_report import PaymentReport
from jamiiwallet.models.transaction import Transaction
from jamiiwallet.models.wallet import Wallet
from payments.models.payment_link import PaymentLink
from payments.models.scheduled_payment import ScheduledPayment
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class PaymentReportService:
    """
    Service for generating payment reports and analytics
    """
    
    def generate_report(self, user, report_type, start_date, end_date, filters=None):
        """
        Generate a payment report
        """
        try:
            with db_txn.atomic():
                # Create report record
                report = PaymentReport.objects.create(
                    user=user,
                    report_type=report_type,
                    start_date=start_date,
                    end_date=end_date,
                    filters=filters or {},
                    status=PaymentReport.Status.GENERATING
                )
                
                # Generate report data asynchronously
                self._generate_report_data_async(report)
                
                return report
                
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise
    
    def _generate_report_data_async(self, report):
        """
        Generate report data asynchronously (Celery task)
        """
        from jamiitasks.tasks.payment_tasks import generate_report_data_task
        generate_report_data_task.delay(report.id)
    
    def generate_transaction_summary(self, report):
        """
        Generate transaction summary report
        """
        try:
            transactions = Transaction.objects.filter(
                created_at__range=(report.start_date, report.end_date),
                wallet__user=report.user
            )
            
            # Apply filters
            if report.filters.get('transaction_type'):
                transactions = transactions.filter(
                    transaction_type=report.filters['transaction_type']
                )
            
            if report.filters.get('status'):
                transactions = transactions.filter(
                    status=report.filters['status']
                )
            
            summary_data = {
                'total_transactions': transactions.count(),
                'total_amount': transactions.aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0.00'),
                'successful_transactions': transactions.filter(
                    status=Transaction.TransactionStatus.COMPLETED
                ).count(),
                'failed_transactions': transactions.filter(
                    status=Transaction.TransactionStatus.FAILED
                ).count(),
                'average_transaction_amount': transactions.aggregate(
                    avg=Avg('amount')
                )['avg'] or Decimal('0.00'),
                'transactions_by_type': list(
                    transactions.values('transaction_type')
                    .annotate(count=Count('id'), total=Sum('amount'))
                    .order_by('-total')
                ),
                'transactions_by_status': list(
                    transactions.values('status')
                    .annotate(count=Count('id'))
                    .order_by('-count')
                ),
                'daily_breakdown': list(
                    transactions.extra({'date': "date(created_at)"})
                    .values('date')
                    .annotate(
                        count=Count('id'),
                        total=Sum('amount')
                    )
                    .order_by('date')
                )
            }
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Failed to generate transaction summary: {e}")
            raise
    
    def generate_revenue_analysis(self, report):
        """
        Generate revenue analysis report
        """
        try:
            # Get all completed transactions for the user
            transactions = Transaction.objects.filter(
                created_at__range=(report.start_date, report.end_date),
                wallet__user=report.user,
                status=Transaction.TransactionStatus.COMPLETED
            )
            
            revenue_data = {
                'total_revenue': transactions.aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0.00'),
                'revenue_by_type': list(
                    transactions.values('transaction_type')
                    .annotate(total=Sum('amount'))
                    .order_by('-total')
                ),
                'monthly_revenue': list(
                    transactions.extra({'month': "strftime('%%Y-%%m', created_at)"})
                    .values('month')
                    .annotate(total=Sum('amount'))
                    .order_by('month')
                ),
                'top_transactions': list(
                    transactions.order_by('-amount')[:10].values(
                        'reference', 'amount', 'transaction_type', 'created_at'
                    )
                )
            }
            
            return revenue_data
            
        except Exception as e:
            logger.error(f"Failed to generate revenue analysis: {e}")
            raise
    
    def generate_user_activity_report(self, report):
        """
        Generate user activity report
        """
        try:
            # Get wallet activity
            wallet = Wallet.objects.get(user=report.user)
            
            activity_data = {
                'wallet_balance': wallet.balance,
                'total_deposits': Transaction.objects.filter(
                    wallet=wallet,
                    transaction_type=Transaction.TransactionType.TOP_UP,
                    status=Transaction.TransactionStatus.COMPLETED,
                    created_at__range=(report.start_date, report.end_date)
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
                'total_withdrawals': Transaction.objects.filter(
                    wallet=wallet,
                    transaction_type=Transaction.TransactionType.WITHDRAWAL,
                    status=Transaction.TransactionStatus.COMPLETED,
                    created_at__range=(report.start_date, report.end_date)
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
                'total_transfers': Transaction.objects.filter(
                    wallet=wallet,
                    transaction_type=Transaction.TransactionType.TRANSFER,
                    status=Transaction.TransactionStatus.COMPLETED,
                    created_at__range=(report.start_date, report.end_date)
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
                'payment_links_created': PaymentLink.objects.filter(
                    created_by=report.user,
                    created_at__range=(report.start_date, report.end_date)
                ).count(),
                'scheduled_payments': ScheduledPayment.objects.filter(
                    created_by=report.user,
                    created_at__range=(report.start_date, report.end_date)
                ).count()
            }
            
            return activity_data
            
        except Exception as e:
            logger.error(f"Failed to generate user activity report: {e}")
            raise
    
    def generate_gateway_performance_report(self, report):
        """
        Generate gateway performance report
        """
        try:
            transactions = Transaction.objects.filter(
                created_at__range=(report.start_date, report.end_date),
                wallet__user=report.user
            )
            
            # Extract gateway information from receipt
            gateway_data = {}
            for txn in transactions:
                receipt = txn.receipt or {}
                gateway = receipt.get('provider', 'UNKNOWN')
                
                if gateway not in gateway_data:
                    gateway_data[gateway] = {
                        'total_transactions': 0,
                        'successful': 0,
                        'failed': 0,
                        'total_amount': Decimal('0.00')
                    }
                
                gateway_data[gateway]['total_transactions'] += 1
                gateway_data[gateway]['total_amount'] += txn.amount
                
                if txn.status == Transaction.TransactionStatus.COMPLETED:
                    gateway_data[gateway]['successful'] += 1
                elif txn.status == Transaction.TransactionStatus.FAILED:
                    gateway_data[gateway]['failed'] += 1
            
            performance_data = {
                'gateways': gateway_data,
                'success_rate_by_gateway': {
                    gateway: (data['successful'] / data['total_transactions'] * 100 
                             if data['total_transactions'] > 0 else 0)
                    for gateway, data in gateway_data.items()
                },
                'average_amount_by_gateway': {
                    gateway: data['total_amount'] / data['total_transactions']
                    for gateway, data in gateway_data.items()
                    if data['total_transactions'] > 0
                }
            }
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to generate gateway performance report: {e}")
            raise
    
    def generate_daily_summary(self, report):
        """
        Generate daily summary report
        """
        try:
            from django.db.models import Count, Sum
            
            summary_data = {
                'date': timezone.now().date().isoformat(),
                'daily_transactions': Transaction.objects.filter(
                    wallet__user=report.user,
                    created_at__date=timezone.now().date()
                ).aggregate(
                    count=Count('id'),
                    total=Sum('amount')
                ),
                'wallet_snapshot': {
                    'balance': Wallet.objects.get(user=report.user).balance,
                    'last_updated': timezone.now()
                },
                'active_payment_links': PaymentLink.objects.filter(
                    created_by=report.user,
                    status=PaymentLink.Status.ACTIVE,
                    expires_at__gt=timezone.now()
                ).count(),
                'pending_scheduled_payments': ScheduledPayment.objects.filter(
                    created_by=report.user,
                    status=ScheduledPayment.Status.SCHEDULED,
                    schedule_date__gte=timezone.now()
                ).count()
            }
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Failed to generate daily summary: {e}")
            raise
    
    def generate_scheduled_reports(self):
        """
        Generate all scheduled reports
        """
        try:
            # This would typically run daily for users who have scheduled reports
            # For now, return empty result
            return {'generated_reports': 0}
            
        except Exception as e:
            logger.error(f"Failed to generate scheduled reports: {e}")
            return {'generated_reports': 0, 'error': str(e)}