# search/views/staff_profile_search_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from elasticsearch_dsl.query import Q

from search.documents.staff_profile_document import StaffProfileDocument
from search.serializers.staff_profile_search_serializer import StaffProfileSearchSerializer


class StaffProfileSearchView(APIView):
    """
    Search staff profiles by institution, department, position etc.

    Rewritten as a plain APIView using elasticsearch_dsl Q objects directly
    (matching every other view in this app) instead of
    django_elasticsearch_dsl_drf's FilteringFilterBackend/CompoundSearchFilterBackend,
    which require a ViewSet's `.action` attribute and raised
    AttributeError on this ListAPIView regardless of whether Elasticsearch
    was enabled - a pre-existing structural bug, not specific to the dev
    fallback.
    """
    # Staff PII (title, phone, institution/department) - authenticated only.
    # NOTE: no institution scoping beyond login - any authenticated user can
    # currently list every institution's staff via institution_id/department_id
    # filters, not just their own.
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        institution_id = request.query_params.get("institution_id")
        department_id = request.query_params.get("department_id")
        is_active = request.query_params.get("is_active")
        page = int(request.query_params.get("page", 1))
        page_size = min(int(request.query_params.get("page_size", 10)), 100)

        search_query = Q("match_all")
        if query:
            search_query = Q(
                "multi_match",
                query=query,
                fields=["position", "title", "user.full_name", "user.email", "institution.name", "department.name"],
            )

        s = StaffProfileDocument.search().query(search_query)

        if institution_id:
            s = s.filter("term", institution_id=institution_id)
        if department_id:
            s = s.filter("term", **{"department.id": department_id})
        if is_active is not None:
            s = s.filter("term", is_active=is_active.lower() == "true")

        start = (page - 1) * page_size
        end = start + page_size
        results = s[start:end].execute()

        serializer = StaffProfileSearchSerializer(results, many=True)
        return Response({
            "results": serializer.data,
            "total": results.hits.total.value,
            "page": page,
            "page_size": page_size,
        }, status=status.HTTP_200_OK)
