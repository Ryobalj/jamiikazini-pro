import pytest
from rest_framework.test import APIClient
from rest_framework import status
from businesses.models.review import Review

pytestmark = pytest.mark.django_db


class TestReviewViewSet:
    @pytest.fixture
    def setup_data(self, setup_review):
        """Hutengeneza review iliyopitishwa na review isiyopitishwa."""
        review_approved = setup_review["review"]
        review_approved.is_approved = True
        review_approved.save()
        review_not_approved = Review.objects.create(
            user=setup_review["user"],
            product=setup_review["product"],
            rating=3,
            content="Haijapitishwa",
            is_approved=False,
        )
        return {
            "user": setup_review["user"],
            "other_user": setup_review["business"].owner,
            "product": setup_review["product"],
            "service": setup_review["service"],
            "approved": review_approved,
            "unapproved": review_not_approved,
        }

    def test_list_only_approved(self, setup_data):
        """Reviews zisizopitishwa zisirudishwe."""
        client = APIClient()
        response = client.get("/api/v1/reviews/")
        assert response.status_code == status.HTTP_200_OK
        ids = [str(r["id"]) for r in response.data]
        assert str(setup_data["approved"].id) in ids
        assert str(setup_data["unapproved"].id) not in ids

    def test_filter_by_target(self, setup_data):
        """Hakikisha filter ya target_type na target_id inafanya kazi."""
        client = APIClient()
        url = f"/api/v1/reviews/?target_type=product&target_id={setup_data['product'].id}"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        ids = [str(r["id"]) for r in response.data]
        assert str(setup_data["approved"].id) in ids

    def test_create_review(self, setup_data):
        """User anaweza kuunda review mpya kwa target moja tu."""
        client = APIClient()
        client.force_authenticate(user=setup_data["user"])
        payload = {
            "product": str(setup_data["product"].id),
            "rating": 5,
            "content": "Nzuri sana!",
        }
        response = client.post("/api/v1/reviews/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Review hii tayari ipo" in str(response.data)

    def test_update_own_review(self, setup_data):
        """User anaweza kubadilisha review yake pekee."""
        client = APIClient()
        client.force_authenticate(user=setup_data["user"])
        payload = {"rating": 1}
        url = f"/api/v1/reviews/{setup_data['approved'].id}/"

        response = client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        setup_data["approved"].refresh_from_db()
        assert setup_data["approved"].rating == 1

    def test_forbid_update_other_user(self, setup_data):
        """Huwezi kubadilisha review ya mtumiaji mwingine."""
        client = APIClient()
        client.force_authenticate(user=setup_data["other_user"])
        url = f"/api/v1/reviews/{setup_data['approved'].id}/"

        response = client.patch(url, {"rating": 2}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_forbid_delete_other_user(self, setup_data):
        """Huwezi kufuta review ya mtumiaji mwingine."""
        client = APIClient()
        client.force_authenticate(user=setup_data["other_user"])
        url = f"/api/v1/reviews/{setup_data['approved'].id}/"

        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN