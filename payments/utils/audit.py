# payments/utils/audit.py

from payments.models.audit_log import AuditLog

def log_payment_audit(user, action: str, description: str, metadata=None, ip="0.0.0.0"):
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            description=description,
            metadata=metadata or {},
            ip_address=ip,
        )
    except Exception:
        pass