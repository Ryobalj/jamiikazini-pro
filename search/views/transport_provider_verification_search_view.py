# search/views/transport_provider_verification_search_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from search.documents.transport_provider_verification_document import TransportProviderVerificationDocument
from search.serializers.transport_provider_verification_search_serializer import TransportProviderVerificationSearchSerializer


class TransportProviderVerificationSearchView(APIView):
    # Regulated compliance data (NIDA/driving-license/vehicle/LATRA status,
    # free-text notes) - authenticated only. NOTE: no institution scoping
    # beyond login - this is the most sensitive entity in this app and still
    # needs real tenant isolation before wider rollout.
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        institution_id = request.GET.get('institution_id', None)
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 50)), 100)

        search = TransportProviderVerificationDocument.search()

        if query:
            search = search.query("multi_match", query=query, fields=[
                "user.username",
                "user.email",
                "institution.name",
                "notes"
            ])

        if institution_id:
            # Institution is UUID-keyed - filter on the raw string, not int().
            search = search.filter("term", institution_id=institution_id)

        start = (page - 1) * page_size
        end = start + page_size
        results = search[start:end].execute()
        serializer = TransportProviderVerificationSearchSerializer(results, many=True)

        return Response({
            "results": serializer.data,
            "page": page,
            "page_size": page_size,
        }, status=status.HTTP_200_OK)
