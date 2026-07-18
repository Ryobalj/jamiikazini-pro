# search/views/review_search_view.py
# Maelezo: View ya kutafuta maoni (reviews) kutoka Elasticsearch

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from elasticsearch_dsl.query import Q
from search.documents.review_document import ReviewDocument
from search.serializers.review_search_serializer import ReviewSearchSerializer


class ReviewSearchView(APIView):
    # Public catalog data - reviews are shown to any shopper on a storefront.
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.GET.get('q', '')

        search_query = Q("match_all")
        if query:
            search_query = Q(
                "multi_match",
                query=query,
                fields=[
                    "content^2",
                    "user.username",
                    "business.name",
                    "product.name",
                    "service.name",
                ]
            )

        search = ReviewDocument.search().query(search_query)
        response = search.execute()
        serializer = ReviewSearchSerializer(response, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)