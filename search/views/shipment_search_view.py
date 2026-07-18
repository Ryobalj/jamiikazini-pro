# search/views/shipment_search_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from elasticsearch_dsl.query import Q, Bool

from search.documents.shipment_document import ShipmentDocument
from search.serializers.shipment_search_serializer import ShipmentSearchSerializer


class ShipmentSearchView(APIView):
    # Shipment data (sender/receiver PII, cost/commission) - authenticated
    # only. NOTE: no sender/receiver/institution scoping beyond login yet.
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        status_filter = request.query_params.get("status")
        transport_mode = request.query_params.get("mode")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        # Start with a bool query
        bool_query = Bool()

        if query:
            bool_query.must = Q("multi_match", query=query, fields=[
                "product.name",
                "product.description",
                "sender.username",
                "receiver.username",
                "transport_providers.name"
            ])
        else:
            bool_query.must = Q("match_all")

        if status_filter:
            bool_query.filter.append(Q("term", status=status_filter))

        if transport_mode:
            bool_query.filter.append(Q("term", preferred_transport_modes=transport_mode))

        # Execute query
        search = ShipmentDocument.search().query(bool_query)
        search = search[(page - 1) * page_size : page * page_size]
        results = search.execute()

        # Pagination metadata
        total = results.hits.total.value if hasattr(results.hits.total, 'value') else results.hits.total
        total_pages = (total + page_size - 1) // page_size

        serializer = ShipmentSearchSerializer(results, many=True)
        return Response({
            "results": serializer.data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_results": total,
                "total_pages": total_pages
            }
        }, status=status.HTTP_200_OK)