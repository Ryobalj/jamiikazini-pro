# search/views/business_search_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from elasticsearch_dsl.query import Q

from search.documents.business_document import BusinessDocument
from search.serializers.business_search_serializer import BusinessSearchSerializer


class BusinessSearchView(APIView):
    # Public catalog data - matches businesses/views/nearby_views.py's AllowAny listing.
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.GET.get('q', '')
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        radius = request.GET.get('radius', '20km')

        search_query = Q("match_all")

        if query:
            search_query = Q(
                "multi_match",
                query=query,
                fields=[
                    "name^3",
                    "description",
                    "category.name",
                    "category.description"
                ]
            )

        if lat and lon:
            location_filter = Q("geo_distance", distance=radius, location={"lat": lat, "lon": lon})
            search_query = search_query & location_filter

        search = BusinessDocument.search().query(search_query)
        response = search.execute()
        serializer = BusinessSearchSerializer(response, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)