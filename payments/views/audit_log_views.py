# payments/views/audit_log_views.py

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from payments.models.audit_log import AuditLog
from payments.serializers.audit_log_serializer import (
    AuditLogSerializer,
    AuditLogCreateSerializer,
)
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from payments.views.base import BaseReadOnlyViewSet
from kiini.models.institution import Institution
from businesses.models.business import Business


class AuditLogViewSet(BaseReadOnlyViewSet):
    permission_classes = [permissions.IsAuthenticated]  # 🔹 essential

    """
    Read-only viewset kwa Audit Logs:
    - Superuser: anaona zote
    - Provider: anaona logs za biashara/taasisi zake + logs zake binafsi
    - Normal user: logs zake binafsi tu
    """
    queryset = AuditLog.objects.select_related("user", "content_type")
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]  # 🔹 essential
    filterset_fields = ["user", "action", "content_type", "object_id"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return AuditLog.objects.none()

        if user.is_superuser:
            return self.queryset

        if getattr(user, "role", None) == "Provider":
            institution_ct = ContentType.objects.get_for_model(Institution)
            business_ct = ContentType.objects.get_for_model(Business)

            # institutions & businesses owned by this provider
            user_institution_ids = user.institutions.values_list("id", flat=True)
            user_business_ids = user.businesses.values_list("id", flat=True)

            return self.queryset.filter(
                Q(content_type=institution_ct, object_id__in=user_institution_ids)
                | Q(content_type=business_ct, object_id__in=user_business_ids)
                | Q(user=user)
            )

        # Normal user -> logs zake binafsi tu
        return self.queryset.filter(user=user)


class AuditLogCreateAPIView(APIView):
    """
    API ya ku-create AuditLog. Inatumika kwa internal usage (service layers, Celery tasks).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AuditLogCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        log = serializer.save(user=request.user)
        return Response({"id": log.id}, status=201)