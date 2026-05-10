# businesses/filters.py
import django_filters
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from .models import Business

class BusinessFilter(django_filters.FilterSet):
    lat = django_filters.NumberFilter(method='filter_by_distance')
    lng = django_filters.NumberFilter(method='filter_by_distance')
    category = django_filters.UUIDFilter(field_name='category__id')
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Business
        fields = ['category', 'is_active']

    def filter_by_distance(self, queryset, name, value):
        lat = self.data.get('lat')
        lng = self.data.get('lng')
        if lat and lng:
            user_location = Point(float(lng), float(lat), srid=4326)
            return queryset.annotate(distance=Distance('location', user_location)).order_by('distance')
        return queryset