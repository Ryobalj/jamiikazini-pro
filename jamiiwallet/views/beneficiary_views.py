# jamiiwallet/views/beneficiary_views.py

from rest_framework import viewsets, permissions

from jamiiwallet.models.beneficiary import Beneficiary
from jamiiwallet.serializers.beneficiary_serializer import BeneficiarySerializer


class BeneficiaryViewSet(viewsets.ModelViewSet):
    """CRUD ya wapokeaji waliohifadhiwa - kila mtumiaji anaona zake tu."""
    serializer_class = BeneficiarySerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return Beneficiary.objects.filter(owner=self.request.user)
