# search/serializers/review_search_serializer.py
# Maelezo: Serializer ya ReviewDocument kwa ajili ya kuwasilisha data kutoka Elasticsearch

from rest_framework import serializers

class ReviewSearchSerializer(serializers.Serializer):
    id = serializers.CharField()
    rating = serializers.FloatField()
    content = serializers.CharField()
    is_approved = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    user = serializers.DictField()
    business = serializers.DictField()
    product = serializers.DictField()
    service = serializers.DictField()