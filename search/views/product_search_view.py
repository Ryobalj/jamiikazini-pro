# search/views/product_search_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from elasticsearch_dsl.query import Q
from search.documents.product_document import ProductDocument
from search.serializers.product_search_serializer import ProductSearchSerializer


class ProductSearchPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


class ProductSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        language_code = request.query_params.get('lang', 'en')

        s = ProductDocument.search()

        # Filter by language
        s = s.filter('term', language_code=language_code)

        # Full-text search on name, description, tags
        if query:
            q = Q("multi_match", query=query, fields=[
                "name^3", "description", "tags", "category.name"
            ])
            s = s.query(q)

        # Sort by distance if coordinates provided
        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)
                s = s.sort({
                    "_geo_distance": {
                        "location": {
                            "lat": lat,
                            "lon": lon
                        },
                        "order": "asc",
                        "unit": "km"
                    }
                })
                # Add script field for distance if needed
                s = s.extra(script_fields={
                    "distance": {
                        "script": {
                            "source": "doc['location'].arcDistance(params.lat, params.lon)",
                            "params": {
                                "lat": lat,
                                "lon": lon
                            }
                        }
                    }
                })
            except ValueError:
                pass

        # Pagination
        paginator = ProductSearchPagination()
        page = paginator.paginate_queryset(s.execute(), request)
        serializer = ProductSearchSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)