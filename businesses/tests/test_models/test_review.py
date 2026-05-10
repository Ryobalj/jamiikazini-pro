# businesses/tests/test_models/test_review.py

import pytest
from django.utils import timezone
from businesses.models.review import Review
from businesses.models.product import Product
from businesses.models.service import Service
from businesses.models.business import Business
from kiini.models.institution import Institution
from accounts.models import User

pytestmark = pytest.mark.django_db

class TestReviewModel:
    def setup_method(self):
        self.institution = Institution.objects.create(name="Tech Hub", domain="techhub")
        self.user = User.objects.create_user(email="client@techhub.com", full_name="Client User", password="secret", institution=self.institution)
        self.owner = User.objects.create_user(email="owner@techhub.com", full_name="Owner User", password="secret", institution=self.institution)
        self.business = Business.objects.create(name="Tech Hub Solutions", slug="techhub", owner=self.owner, institution=self.institution)

        self.product = Product.objects.create(name="Smartwatch", price=120000, business=self.business, language_code="en", is_available=True)
        self.service = Service.objects.create(name="Phone Repair", price=40000, business=self.business)

    def test_create_review_for_product(self):
        review = Review.objects.create(
            user=self.user,
            rating=4,
            content="Very useful product!",
            product=self.product,
            is_approved=True,
        )

        expected_str = f"{self.user.username}'s Review on {self.product}"
        assert str(review) == expected_str
        assert review.product == self.product
        assert review.service is None
        assert review.business is None

    def test_create_review_for_service(self):
        review = Review.objects.create(
            user=self.user,
            rating=5,
            content="Fixed my phone fast!",
            service=self.service,
        )

        assert review.service == self.service
        assert review.product is None
        assert review.business is None

    def test_review_requires_at_least_one_target(self):
        with pytest.raises(Exception):
            Review.objects.create(user=self.user, rating=3, content="No target")

    def test_review_rating_limits(self):
        review = Review.objects.create(
            user=self.user,
            rating=5,
            comment="Excellent",
            product=self.product
        )
        assert review.rating in [1, 2, 3, 4, 5]