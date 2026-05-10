# search/views/staff_profile_search_view.py

from rest_framework.generics import ListAPIView
from django_elasticsearch_dsl_drf.viewsets import BaseDocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    CompoundSearchFilterBackend,
)
from django_elasticsearch_dsl_drf.pagination import PageNumberPagination
from search.documents.staff_profile_document import StaffProfileDocument
from search.serializers.staff_profile_search_serializer import StaffProfileSearchSerializer


class StaffProfileSearchPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class StaffProfileSearchView(ListAPIView):
    """
    Search staff profiles by institution, department, position etc.
    """
    document = StaffProfileDocument
    serializer_class = StaffProfileSearchSerializer
    pagination_class = StaffProfileSearchPagination
    filter_backends = [
        FilteringFilterBackend,
        CompoundSearchFilterBackend,
    ]

    search_fields = [
        'position',
        'title',
        'user.full_name',
        'user.email',
        'institution.name',
        'department.name',
    ]

    filter_fields = {
        'institution_id': 'institution_id',
        'is_active': 'is_active',
        'department.id': 'department.id',
    }

    def get_queryset(self):
        return self.document.search()