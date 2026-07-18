# kiini/views/institution_public_views.py

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from kiini.models.institution import Institution
from kiini.serializers.institution_serializers import PublicInstitutionSerializer


class PublicInstitutionDetailView(generics.RetrieveAPIView):
    """
    Ukurasa wa umma wa taasisi (mf. jengo la maduka kama mall) - hauitaji
    kuingia, na unaonyesha maduka (Business) hai chini ya taasisi hii ili
    mteja aweze kuvinjari kama "jengo" moja lenye maduka mengi.
    """
    queryset = Institution.objects.filter(is_active=True)
    serializer_class = PublicInstitutionSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "pk"


class InstitutionResolveDomainView(generics.RetrieveAPIView):
    """
    GET /kiini/institutions/resolve-domain/?domain=<label>
    Sawa na PublicInstitutionDetailView lakini kutafutwa kwa subdomain -
    hutumiwa na frontend wakati mtumiaji anafika kupitia
    <domain>.jamiikazini.com badala ya njia ya kawaida ya /institutions/<uuid>.
    """
    queryset = Institution.objects.filter(is_active=True)
    serializer_class = PublicInstitutionSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        domain = (self.request.query_params.get("domain") or "").strip().lower()
        if not domain:
            raise NotFound("Weka ?domain=.")
        return get_object_or_404(self.get_queryset(), domain=domain)
