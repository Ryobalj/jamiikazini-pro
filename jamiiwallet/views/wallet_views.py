# jamiiwallet/views/wallet_view.py

from rest_framework import generics, permissions
from jamiiwallet.models.wallet import Wallet
from jamiiwallet.serializers.wallet_serializer import WalletSerializer

class WalletDetailView(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Wallet.objects.get(user=self.request.user)