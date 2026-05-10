from rest_framework import generics
from gov_integration.models import ServiceType
from gov_integration.serializers.service_type import ServiceTypeSerializer

class ServiceTypeListView(generics.ListAPIView):
    serializer_class = ServiceTypeSerializer

    def get_queryset(self):
        queryset = ServiceType.objects.filter(is_active=True)
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country__code__iexact=country.strip())
        return queryset