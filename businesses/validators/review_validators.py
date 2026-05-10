# businesses/validators/review_validators.py

from rest_framework import serializers
from businesses.models.review import Review

def validate_unique_review(user, business=None, product=None, service=None):
    """Hakikisha review ni ya kipekee kwa user na target iliyotolewa."""
    if business and Review.objects.filter(user=user, business=business).exists():
        raise serializers.ValidationError("Review hii tayari ipo kwa mtumiaji huyu.")
    if product and Review.objects.filter(user=user, product=product).exists():
        raise serializers.ValidationError("Review hii tayari ipo kwa mtumiaji huyu.")
    if service and Review.objects.filter(user=user, service=service).exists():
        raise serializers.ValidationError("Review hii tayari ipo kwa mtumiaji huyu.")