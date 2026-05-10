# search/views/transport_provider_verification_search_view.py

from django_elasticsearch_dsl.search import Search
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from search.documents.transport_provider_verification_document import TransportProviderVerificationDocument
from search.serializers.transport_provider_verification_search_serializer import TransportProviderVerificationSearchSerializer


class TransportProviderVerificationSearchView(APIView):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        institution_id = request.GET.get('institution_id', None)

        search = TransportProviderVerificationDocument.search()

        if query:
            search = search.query("multi_match", query=query, fields=[
                "user.username",
                "user.email",
                "institution.name",
                "notes"
            ])

        if institution_id:
            search = search.filter("term", institution_id=int(institution_id))

        results = search[:50].execute()
        serializer = TransportProviderVerificationSearchSerializer(results, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)