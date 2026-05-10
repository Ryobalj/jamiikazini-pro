# payments/models/audit_log.py

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from kiini.models.base import TimeStampedModel
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
import uuid
import logging

from security.helpers.encryption import encrypt_data, decrypt_data
from security.helpers.alerts import send_slack_alert

logger = logging.getLogger(__name__)


class AuditAction(models.TextChoices):
    CREATE = "CREATE", _("Create")
    UPDATE = "UPDATE", _("Update")
    DELETE = "DELETE", _("Delete")
    LOGIN = "LOGIN", _("Login")
    LOGOUT = "LOGOUT", _("Logout")
    PAYMENT = "PAYMENT", _("Payment")
    FAILED_2FA = "FAILED_2FA", _("Failed 2FA")  # 🚨 security
    PAYMENT_RETRY = "PAYMENT_RETRY", _("Payment Retry")  # 🚨 security
    OTHER = "OTHER", _("Other")


class AuditLog(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("User"),
        help_text=_("User who performed the action, or null for system actions"),
        db_index=True,
    )
    action = models.CharField(
        max_length=20,
        choices=AuditAction.choices,
        verbose_name=_("Action"),
        db_index=True,
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Target Content Type"),
        help_text=_("Model type of the affected object"),
        db_index=True,
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Target Object ID"),
        help_text=_("UUID of the affected object"),
        db_index=True,
    )
    target_object = GenericForeignKey("content_type", "object_id")

    # 🔐 Encrypted fields
    _description = models.TextField(
        blank=True,
        db_column="description",
        verbose_name=_("Description (Encrypted)"),
        help_text=_("Additional details about the action (encrypted)"),
    )
    _metadata = models.JSONField(
        blank=True,
        null=True,
        db_column="metadata",
        verbose_name=_("Metadata (Encrypted)"),
        help_text=_("Additional structured data about the action (encrypted)"),
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_("IP Address"),
        help_text=_("IP address from where the action was performed"),
    )

    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["action"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    @property
    def description(self):
        if not self._description:
            return None
        try:
            return decrypt_data(self._description)
        except Exception:
            return "[DECRYPTION FAILED]"

    @description.setter
    def description(self, value):
        if value is None:
            self._description = None
        else:
            self._description = encrypt_data(value)

    @property
    def metadata(self):
        if not self._metadata:
            return None
        try:
            decrypted = decrypt_data(str(self._metadata))
            import json
            return json.loads(decrypted)
        except Exception:
            return {}

    @metadata.setter
    def metadata(self, value):
        if value is None:
            self._metadata = None
        else:
            import json
            self._metadata = encrypt_data(json.dumps(value))

    def __str__(self):
        user_display = (
            self.user.full_name
            if self.user and hasattr(self.user, "full_name")
            else (self.user or _("System"))
        )
        target_display = (
            f"{self.content_type} ({self.object_id})"
            if self.content_type and self.object_id
            else _("N/A")
        )
        return _("{action} on {target} by {user}").format(
            action=self.get_action_display(),
            target=target_display,
            user=user_display,
        )

    def clean(self):
        if self.object_id:
            try:
                uuid.UUID(str(self.object_id))
            except ValueError:
                raise ValidationError({"object_id": _("Invalid UUID format.")})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def log_action(user, action, target_obj=None, description="", metadata=None, ip_address=None):
        """
        Helper method to create an audit log entry.
        - user: User performing the action, or None for system.
        - action: Action string from AuditAction.
        - target_obj: The model instance affected.
        - description: Optional textual description (encrypted).
        - metadata: Optional dict/json data (encrypted).
        - ip_address: Optional IP string.
        """
        content_type = None
        object_id = None
        if target_obj:
            content_type = ContentType.objects.get_for_model(target_obj)
            object_id = getattr(target_obj, "pk", None)
            if object_id and not isinstance(object_id, uuid.UUID):
                try:
                    object_id = uuid.UUID(str(object_id))
                except Exception:
                    object_id = str(object_id)

        log_entry = AuditLog.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=object_id,
            description=description,
            metadata=metadata or {},
            ip_address=ip_address,
        )

        # 🚨 Auto Slack Alerts for sensitive actions
        if action in [AuditAction.FAILED_2FA, AuditAction.PAYMENT_RETRY]:
            try:
                send_slack_alert(
                    f"[SECURITY ALERT] action={action} user={getattr(user, 'id', None)} desc={description}"
                )
            except Exception as e:
                logger.error("Failed to send Slack alert for audit log: %s", e)

        return log_entry

    @staticmethod
    def log_from_request(request, user, action, target_obj=None, description="", metadata=None):
        """
        Shortcut for logging with IP auto-detection from request.
        """
        ip_address = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR")
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()
        return AuditLog.log_action(
            user=user,
            action=action,
            target_obj=target_obj,
            description=description,
            metadata=metadata,
            ip_address=ip_address,
        )