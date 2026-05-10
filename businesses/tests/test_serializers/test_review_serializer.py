import pytest
from businesses.models.review import Review
from businesses.serializers.review_serializer import ReviewSerializer
from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from businesses.models.product import Product
from businesses.models.service import Service
from accounts.models import User
from kiini.models.institution import Institution
from unittest import mock


@pytest.mark.django_db
class TestReviewSerializer:

    @pytest.fixture
    def setup_review(self):
        institution = Institution.objects.create(name="Jamii Org")
        user = User.objects.create_user(email="client@jamii.com", password="pass123", full_name="Client Name",
                                        institution=institution)

        owner = User.objects.create_user(email="owner@jamii.com", password="pass123", full_name="Owner",
                                          institution=institution)
        business = Business.objects.create(name="Huduma Co", owner=owner, institution=institution)
        category = BusinessCategory.objects.create(name="Afya", slug="afya")

        product = Product.objects.create(
            business=business,
            name="Sabuni Asili",
            slug="sabuni-asili",
            type="physical",
            price=1000,
            currency="TZS",
            quantity_in_stock=10,
            unit="pcs",
            is_available=True,
            is_featured=False,
            language_code="sw",
            tax_inclusive=True,
            tax_rate=18,
        )

        service = Service.objects.create(
            business=business,
            category=category,
            name="Ushauri wa Bure",
            price=0,
            billing_type="per_hour",
            location_type="online",
            requires_booking=False,
            is_available=True
        )

        review = Review.objects.create(
            user=user,
            product=product,
            rating=4,
            content="Nzuri sana!"
        )
        return {
            "user": user,
            "business": business,
            "product": product,
            "service": service,
            "review": review
        }

    def test_review_serializer_output(self, setup_review):
        serializer = ReviewSerializer(instance=setup_review["review"])
        data = serializer.data
        assert data["id"] == str(setup_review["review"].id)
        assert data["rating"] == 4
        assert data["content"] == "Nzuri sana!"
        assert data["is_approved"] is False
        assert "target" in data
        assert data["target"] == str(setup_review["product"])
        assert data["username"] == setup_review["user"].username

    def test_review_serializer_requires_one_target(self, setup_review, rf):
        payload = {
            "product": str(setup_review["product"].id),
            "service": str(setup_review["service"].id),
            "rating": 3,
            "content": "Haikuwa mbaya",
        }

        request = rf.post("/fake-url/")
        request.user = setup_review["user"]

        serializer = ReviewSerializer(data=payload, context={"request": request})
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
        assert "Tafadhali toa review kwa kipengele kimoja tu" in serializer.errors["non_field_errors"][0]

    def test_review_serializer_create_valid_review(self, setup_review, rf):
        payload = {
            "service": str(setup_review["service"].id),
            "rating": 5,
            "content": "Huduma bora!",
        }

        request = rf.post("/api/reviews/")
        request.user = setup_review["user"]

        with mock.patch("businesses.serializers.review_serializer.validate_unique_review") as mocked_validate:
            mocked_validate.return_value = None
            serializer = ReviewSerializer(data=payload, context={"request": request})
            assert serializer.is_valid(), serializer.errors
            review = serializer.save()
            assert review.user == setup_review["user"]
            assert review.service == setup_review["service"]
            assert review.rating == 5
            assert review.content == "Huduma bora!"

    def test_review_serializer_prevents_duplicate(self, setup_review, rf):
        """Hakikisha review maradufu inazuiwa na inarejesha 'non_field_errors'."""
        payload = {
            "product": setup_review["product"].id,  # ✅ ID bila str()
            "rating": 5,
            "content": "Naipenda hii!",
        }
    
        request = rf.post("/api/reviews/")
        request.user = setup_review["user"]
    
        serializer = ReviewSerializer(data=payload, context={"request": request})
        assert not serializer.is_valid(), serializer.errors
        assert "non_field_errors" in serializer.errors
        assert "Review hii tayari ipo kwa mtumiaji huyu." in serializer.errors["non_field_errors"][0]