# File: search/views/branch_search_view.py
# Maelezo: View ya kutafuta matawi (branches) kutoka Elasticsearch

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from elasticsearch_dsl.query import Q
from search.documents.branch_document import BranchDocument
from search.serializers.branch_search_serializer import BranchSearchSerializer


class BranchSearchView(APIView):
    # Public catalog data - matches businesses/views/branch_views.py's public listing.
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.GET.get('q', '')
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        radius = request.GET.get('radius', '10km')

        search_query = Q("match_all")

        if query:
            search_query = Q(
                "multi_match",
                query=query,
                fields=[
                    "name^3",
                    "description",
                    "business.name",
                    "services.name"
                ]
            )

        if lat and lon:
            location_filter = Q("geo_distance", distance=radius, location={"lat": lat, "lon": lon})
            search_query = search_query & location_filter

        search = BranchDocument.search().query(search_query)
        response = search.execute()
        serializer = BranchSearchSerializer(response, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)