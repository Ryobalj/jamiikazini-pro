# businesses/views/public_views.py

from rest_framework import generics, permissions
from businesses.models.business import Business
from businesses.serializers.business_serializer import BusinessDetailSerializer

class PublicBusinessDetailView(generics.RetrieveAPIView):
    queryset = Business.objects.filter(is_active=True)
    serializer_class = BusinessDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'