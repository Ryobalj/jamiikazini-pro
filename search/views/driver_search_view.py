# search/views/driver_search_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from elasticsearch_dsl.query import Q

from search.documents.driver_document import DriverDocument
from search.serializers.driver_search_serializer import DriverSearchSerializer


class DriverSearchView(APIView):
    # Driver PII (phone, license) - authenticated only. NOTE: there is no
    # institution/ownership scoping here beyond login - any authenticated
    # user can currently search drivers across every transport provider.
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = DriverSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        query = Q("match_all")

        if q := data.get("q"):
            query = Q("multi_match", query=q, fields=["full_name", "license_number"])

        s = DriverDocument.search().query(query)

        if provider_id := data.get("provider_id"):
            s = s.filter("term", transport_provider_id=provider_id)

        page = data["page"]
        per_page = data["per_page"]
        start = (page - 1) * per_page
        end = start + per_page

        results = s[start:end].execute()

        return Response({
            "total": results.hits.total.value,
            "results": [hit.to_dict() for hit in results]
        }, status=status.HTTP_200_OK)