# search/views/search.py

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from django_elasticsearch_dsl.search import Search
from elasticsearch_dsl import Q

from search.documents.product_document import ProductDocument
from search.documents.service_document import ServiceDocument
from search.documents.business_document import BusinessDocument
from search.documents.branch_document import BranchDocument
from search.documents.department_document import DepartmentDocument
from search.documents.driver_document import DriverDocument
from search.documents.shipment_document import ShipmentDocument
from search.documents.review_document import ReviewDocument
from search.documents.staff_profile_document import StaffProfileDocument
from search.documents.transport_leg_document import TransportLegDocument
from search.documents.transport_provider_document import TransportProviderDocument
from search.documents.transport_provider_verification_document import TransportProviderVerificationDocument


class UnifiedSearchViewSet(ViewSet):
    def list(self, request):
        query = request.query_params.get('q')
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius = request.query_params.get('radius', '10km')
        institution_id = request.query_params.get('institution_id')
        category_ids = request.query_params.get('category_ids')  # comma separated
        business_ids = request.query_params.get('business_ids')  # comma separated
        sort = request.query_params.get('sort', 'relevance')  # relevance, latest, price_asc, price_desc, proximity

        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 10))
        offset = (page - 1) * size
        type_filter = request.query_params.get('types')

        if not query:
            return Response({"error": "Missing 'q' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        base_query = Q("multi_match", query=query, fields=[
            'name', 'description', 'tags',
            'category.name', 'business.name'
        ])

        user = request.user
        user_role = getattr(user, 'role', None)

        type_map = {
            'product': ('Product', ProductDocument),
            'service': ('Service', ServiceDocument),
            'business': ('Business', BusinessDocument),
            'branch': ('Branch', BranchDocument),
            'department': ('Department', DepartmentDocument),
            'driver': ('Driver', DriverDocument),
            'shipment': ('Shipment', ShipmentDocument),
            'review': ('Review', ReviewDocument),
            'staff_profile': ('Staff', StaffProfileDocument),
            'transport_leg': ('Transport Leg', TransportLegDocument),
            'transport_provider': ('Transport Provider', TransportProviderDocument),
            'transport_provider_verification': ('Provider Verification', TransportProviderVerificationDocument),
        }

        allowed_types = list(type_map.keys())
        selected_types = [t for t in allowed_types if t in (type_filter or ','.join(allowed_types)).split(',')]

        if category_ids:
            category_ids = [int(cid.strip()) for cid in category_ids.split(',')]
        if business_ids:
            business_ids = [int(bid.strip()) for bid in business_ids.split(',')]

        def get_sort_order():
            if sort == 'proximity' and lat and lon:
                return [{
                    "_geo_distance": {
                        "location": {"lat": float(lat), "lon": float(lon)},
                        "order": "asc",
                        "unit": "km"
                    }
                }]
            elif sort == 'latest':
                return ['-created_at']
            elif sort == 'price_asc':
                return ['price']
            elif sort == 'price_desc':
                return ['-price']
            return []  # relevance (default)

        def apply_filters(document_cls):
            s = document_cls.search()
            s = s.query(base_query)

            if lat and lon and sort == 'proximity':
                location_filter = Q('geo_distance', distance=radius, location={"lat": float(lat), "lon": float(lon)})
                s = s.filter(location_filter)

            if institution_id and hasattr(document_cls, 'institution_id'):
                s = s.filter('term', institution_id=institution_id)

            if user_role == 'institution_admin':
                s = s.filter('term', institution_id=user.institution_id)

            if category_ids and hasattr(document_cls, 'category'):
                s = s.filter('terms', category__id=category_ids)

            if business_ids and hasattr(document_cls, 'business'):
                s = s.filter('terms', business__id=business_ids)

            sort_order = get_sort_order()
            if sort_order:
                s = s.sort(*sort_order)

            total = s.count()
            results = s[offset:offset + size].execute()
            return total, results

        def to_card(hit, label):
            return {
                "id": hit.meta.id,
                "name": getattr(hit, 'name', ''),
                "description": getattr(hit, 'description', '')[:120],
                "type": hit.meta.index,
                "type_label": label,
                "location": getattr(hit, 'location', None),
                "category": getattr(hit, 'category', {}).get('name', '') if hasattr(hit, 'category') else '',
                "business": getattr(hit, 'business', {}).get('name', '') if hasattr(hit, 'business') else '',
            }

        combined = []
        total_count = 0
        for key in selected_types:
            label, doc_cls = type_map[key]
            count, hits = apply_filters(doc_cls)
            total_count += count
            combined.extend([to_card(hit, label) for hit in hits])

        return Response({
            "page": page,
            "size": size,
            "total": total_count,
            "results": combined
        }, status=status.HTTP_200_OK)