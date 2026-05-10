# search/serializers/product_search_serializer.py

from rest_framework import serializers

class ProductSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField()
    type = serializers.CharField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    currency = serializers.CharField()
    quantity_in_stock = serializers.IntegerField()
    unit = serializers.CharField()
    is_available = serializers.BooleanField()
    is_featured = serializers.BooleanField()
    image = serializers.ImageField()
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    tax_inclusive = serializers.BooleanField()
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    external_link = serializers.URLField(allow_blank=True, required=False)
    language_code = serializers.CharField()

    business_name = serializers.CharField()
    business_id = serializers.CharField()
    institution_id = serializers.IntegerField()
    location = serializers.DictField()

    category = serializers.DictField()

    distance = serializers.FloatField(required=False)  # For sorted-by-distance results