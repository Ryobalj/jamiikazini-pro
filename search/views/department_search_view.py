# File: search/views/department_search_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from elasticsearch_dsl.query import Q
from search.documents.department_document import DepartmentDocument
from search.serializers.department_search_serializer import DepartmentSearchSerializer


class DepartmentSearchView(APIView):
    # Public directory data - department names/institution are not sensitive.
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.GET.get("q", "")
        institution_id = request.GET.get("institution_id")

        search_query = Q("match_all")
        if query:
            search_query = Q("multi_match", query=query, fields=["name", "institution.name"])

        if institution_id:
            institution_filter = Q("term", institution_id=institution_id)
            search_query = search_query & institution_filter

        search = DepartmentDocument.search().query(search_query)
        response = search.execute()
        serializer = DepartmentSearchSerializer(response, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)