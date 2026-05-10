# search/views/transport_leg_search_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from elasticsearch_dsl.query import Q

from search.documents.transport_leg_document import TransportLegDocument
from search.serializers.transport_leg_search_serializer import TransportLegSearchSerializer


class TransportLegSearchView(APIView):
    def get(self, request):
        serializer = TransportLegSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        query = Q("match_all")

        if q := data.get('q'):
            query = Q("multi_match", query=q, fields=[
                "origin_name", "destination_name", "mode", "status",
                "shipment.status", "provider.name"
            ])

        s = TransportLegDocument.search().query(query)

        lat = data.get('lat')
        lon = data.get('lon')
        if lat and lon:
            location_filter = Q(
                'geo_distance',
                distance=f"{data.get('max_distance', 50)}km",
                current_location={"lat": lat, "lon": lon}
            )
            s = s.filter(location_filter)
            s = s.sort({
                "_geo_distance": {
                    "current_location": {"lat": lat, "lon": lon},
                    "order": "asc",
                    "unit": "km"
                }
            })

        page = data['page']
        per_page = data['per_page']
        start = (page - 1) * per_page
        end = start + per_page
        results = s[start:end].execute()

        return Response({
            "total": results.hits.total.value,
            "results": [hit.to_dict() for hit in results]
        }, status=status.HTTP_200_OK)