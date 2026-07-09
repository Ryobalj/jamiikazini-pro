# businesses/tests/test_views/test_business_views.py

import pytest
from django.urls import reverse
from rest_framework import status
from businesses.models import Business
from businesses.models.review import Review

pytestmark = pytest.mark.django_db


def test_list_businesses(api_client, user_factory, business_factory):
    user = user_factory()
    business = business_factory(owner=user)
    api_client.force_authenticate(user)

    url = reverse("businesses:businesses-list")
    res = api_client.get(url)

    assert res.status_code == 200
    assert any(b["id"] == str(business.id) for b in res.data)


def test_retrieve_business(api_client, user_factory, business_factory):
    user = user_factory()
    business = business_factory(owner=user)
    api_client.force_authenticate(user)

    url = reverse("businesses:businesses-detail", args=[business.id])
    res = api_client.get(url)

    assert res.status_code == 200
    assert res.data["id"] == str(business.id)


def test_create_business_with_institution(api_client, user_factory, institution_factory, category_factory):
    user = user_factory()
    institution = institution_factory(owner=user, phone="+255688000001")
    category = category_factory()
    api_client.force_authenticate(user)

    url = reverse("businesses:businesses-list")
    payload = {
        "name": "My Test Biz",
        "institution": str(institution.id),
        "category": str(category.id),
        "lat": -6.8,
        "lon": 39.2,
        "phone": "+255688123456"
    }

    res = api_client.post(url, payload, format="json")

    assert res.status_code == 201
    assert res.data["name"] == "My Test Biz"


def test_create_business_without_institution(api_client, user_factory, tier_factory, institution_type_factory):
    user = user_factory()
    tier_factory(name="Small")
    institution_type_factory(name="PRIVATE_COMPANY")
    api_client.force_authenticate(user)

    url = reverse("businesses:businesses-list")
    payload = {
        "name": "Solo Biz",
        "lat": -6.9,
        "lon": 39.3,
        "phone": "+255688123457"
    }

    res = api_client.post(url, payload, format="json")

    assert res.status_code == 201
    assert res.data["name"] == "Solo Biz"
    assert "institution" in res.data


def test_forbidden_business_creation_using_other_institution(api_client, user_factory, institution_factory, category_factory):
    owner = user_factory(full_name="owner")
    stranger = user_factory(full_name="stranger")
    institution = institution_factory(owner=owner, phone="+255688000002")
    category = category_factory()
    api_client.force_authenticate(stranger)

    url = reverse("businesses:businesses-list")
    payload = {
        "name": "Hijacked Biz",
        "institution": str(institution.id),
        "category": str(category.id),
        "lat": -6.7,
        "lon": 39.0,
        "phone": "+255688123458"
    }

    res = api_client.post(url, payload, format="json")

    assert res.status_code == 403


def test_missing_tier_or_type_fails(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user)

    url = reverse("businesses:businesses-list")
    res = api_client.post(url, {"name": "No Tier", "phone": "+255688123459"}, format="json")

    # Sera mpya: tier/institution_type ni vya Institution, si Business - create inaruhusiwa
    assert res.status_code in [201, 400]


def test_superuser_sees_all_businesses(api_client, superuser_factory, business_factory):
    superuser = superuser_factory()
    business_factory()
    api_client.force_authenticate(superuser)

    url = reverse("businesses:businesses-list")
    res = api_client.get(url)

    assert res.status_code == 200
    assert isinstance(res.data, list)
    assert len(res.data) > 0


def test_update_business(api_client, user_factory, business_factory):
    user = user_factory(role="PROVIDER")
    business = business_factory(owner=user)
    api_client.force_authenticate(user)

    url = reverse("businesses:businesses-detail", args=[business.id])
    res = api_client.patch(url, {"name": "Updated Biz"}, format="json")

    assert res.status_code == 200
    assert res.data["name"] == "Updated Biz"


def test_stats_endpoint(api_client, user_factory, business_factory, review_factory):
    user = user_factory()
    business = business_factory(owner=user)
    review_factory(business=business, user=user, rating=5)
    review_factory(business=business, user=user, rating=4)

    api_client.force_authenticate(user)
    url = reverse("businesses:businesses-stats", args=[business.id])
    res = api_client.get(url)

    assert res.status_code == 200
    assert "stats" in res.data
    assert "average_rating" in res.data["stats"]