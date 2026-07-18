# search/views/service_search_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from elasticsearch_dsl.query import Q

from search.documents.service_document import ServiceDocument
from search.serializers.service_search_serializer import ServiceSearchSerializer


class ServiceSearchView(APIView):
    # Public catalog data - matches businesses/views/service_views.py's AllowAny nearby action.
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "")
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        category_id = request.query_params.get("category_id")

        search_query = ServiceDocument.search()

        if lat and lon:
            location = {"lat": float(lat), "lon": float(lon)}
            search_query = search_query.sort({
                "_geo_distance": {
                    "location": location,
                    "order": "asc",
                    "unit": "km"
                }
            })

        filters = []

        if query:
            filters.append(
                Q("multi_match", query=query, fields=["name", "description", "business.name", "category.name"])
            )

        if category_id:
            filters.append(Q("term", category__id=category_id))

        if filters:
            search_query = search_query.query("bool", must=filters)

        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 10))
        start = (page - 1) * per_page
        end = start + per_page

        results = search_query[start:end].execute()

        serializer = ServiceSearchSerializer(results, many=True)
        return Response({
            "results": serializer.data,
            "total": results.hits.total.value,
            "page": page,
            "per_page": per_page
        }, status=status.HTTP_200_OK)