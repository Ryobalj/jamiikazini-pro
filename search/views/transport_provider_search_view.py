# search/views/transport_provider_search_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from elasticsearch_dsl.query import Q
from search.documents.transport_provider_document import TransportProviderDocument
from search.serializers.transport_provider_search_serializer import TransportProviderSearchSerializer


class TransportProviderSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = TransportProviderSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        query = Q("match_all")
        if 'q' in data:
            query = Q("multi_match", query=data['q'], fields=[
                "user.username", "user.email"
            ])

        search = TransportProviderDocument.search().query(query)

        if 'lat' in data and 'lon' in data:
            location = {
                "lat": data["lat"],
                "lon": data["lon"]
            }
            search = search.sort({
                "_geo_distance": {
                    "location": location,
                    "order": "asc",
                    "unit": "km"
                }
            })

            if 'max_distance' in data:
                search = search.filter(
                    "geo_distance",
                    distance=f"{data['max_distance']}km",
                    location=location
                )

        page = data.get('page', 1)
        per_page = data.get('per_page', 10)
        start = (page - 1) * per_page
        end = start + per_page

        results = search[start:end].execute()

        hits = [
            {
                "id": hit.meta.id,
                "username": getattr(hit.user, "username", None) if hasattr(hit, "user") else None,
                "email": getattr(hit.user, "email", None) if hasattr(hit, "user") else None,
                "provider_type": getattr(hit, "provider_type", None),
                "institution": getattr(hit.institution, "name", None) if hasattr(hit, "institution") else None,
                "is_approved": getattr(hit, "is_approved", None),
                "location": getattr(hit, "location", None),
                "created_at": getattr(hit, "created_at", None),
            }
            for hit in results
        ]

        return Response({
            "results": hits,
            "total": results.hits.total.value,
            "page": page,
            "per_page": per_page
        }, status=status.HTTP_200_OK)