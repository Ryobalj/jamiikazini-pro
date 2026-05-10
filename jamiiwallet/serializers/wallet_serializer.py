# jamiiwallet/serializers/wallet_serializer.py

from rest_framework import serializers
from jamiiwallet.models.wallet import Wallet

class WalletSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'currency', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'balance', 'currency', 'created_at', 'updated_at']