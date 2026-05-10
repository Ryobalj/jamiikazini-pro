from rest_framework import generics
from gov_integration.models import CountryConfig
from gov_integration.serializers.country_config import CountryConfigSerializer

class CountryListView(generics.ListAPIView):
    queryset = CountryConfig.objects.all()
    serializer_class = CountryConfigSerializer