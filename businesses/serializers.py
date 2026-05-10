# businesses/serializers.py

from rest_framework import serializers
from .models import Business, BusinessCategory, Product
from django.utils.translation import gettext_lazy as _


class BusinessCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCategory
        fields = '__all__'


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class NearbyProductSerializer(serializers.ModelSerializer):
    business = BusinessSerializer()
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'price',
            'is_available',
            'business',
            'distance',
        ]
    
    def get_distance(self, obj):
        if hasattr(obj, 'distance') and obj.distance:
            distance_m = obj.distance.m
            if distance_m < 1000:
                return f"{round(distance_m, 1)} {_('m')}"
            else:
                distance_km = distance_m / 1000
                return f"{round(distance_km, 2)} {_('km')}"
        return None