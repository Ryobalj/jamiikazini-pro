import pytest
from django.contrib.gis.geos import Point
from rest_framework.exceptions import ValidationError

from businesses.serializers.business_serializer import (
    BusinessSerializer,
    BusinessDetailSerializer,
    BusinessMinimalSerializer
)

pytestmark = pytest.mark.django_db


def test_create_business_with_location_and_institution(
    user_factory, category_factory, unique_institution, api_client
):
    user = user_factory()
    category = category_factory()
    payload = {
        "name": "Test Business",
        "description": "Test Desc",
        "phone": "+255714123456",
        "email": "biz@test.com",
        "website": "https://test.com",
        "institution": unique_institution.id,
        "category": category.id,
        "lat": -6.792,
        "lon": 39.208
    }

    serializer = BusinessSerializer(data=payload, context={"request": type("obj", (), {"user": user})})
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.name == payload["name"]
    assert instance.owner == user
    assert instance.location.x == payload["lon"]
    assert instance.location.y == payload["lat"]
    assert instance.institution == unique_institution
    assert instance.category == category


def test_create_business_without_institution_creates_website(
    user_factory, category_factory, api_client, unique_institution
):
    user = user_factory()
    category = category_factory()
    payload = {
        "name": "Cool Shop",
        "email": "cool@biz.com",
        "phone": "+255714123456",
        "category": category.id,
        "lat": -6.5,
        "lon": 39.1
    }

    serializer = BusinessSerializer(data=payload, context={"request": type("obj", (), {"user": user})})
    assert serializer.is_valid(), serializer.errors

    business = serializer.save()
    assert business.website.startswith("cool-shop.") or business.website.endswith(".com")

# test_minimal_serializer_output
def test_minimal_serializer_output(business_factory):
    business = business_factory()
    serializer = BusinessMinimalSerializer(business)
    data = serializer.data
    assert data["id"] == str(business.id)  # ✅ fix UUID comparison
    assert data["name"] == business.name
    assert data["slug"] == business.slug


def test_website_generation_logic(user_factory, category_factory, unique_institution):
    user = user_factory()
    category = category_factory()
    payload = {
        "name": "Test Shop",
        "institution": unique_institution,
        "category": category,
        "email": "shop@me.com"
    }

    serializer = BusinessSerializer(
        data={
            "name": payload["name"],
            "email": payload["email"],
            "institution": unique_institution.id
        },
        context={"request": type("obj", (), {"user": user})}
    )
    assert serializer.is_valid()
    instance = serializer.save()

    expected_slug = "test-shop"
    expected_website = f"{expected_slug}.{unique_institution.domain.lower()}"
    assert instance.website == expected_website


def test_update_business_location(business_factory):
    business = business_factory(location=None)
    serializer = BusinessSerializer(
        instance=business,
        data={"lat": -6.7, "lon": 39.0},
        partial=True,
        context={"request": type("obj", (), {"user": business.owner})}
    )
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()
    assert instance.location.x == 39.0
    assert instance.location.y == -6.7


def test_serializer_get_location_lat_lon(business_factory):
    business = business_factory(location=Point(39.5, -6.3))
    serializer = BusinessSerializer(business)
    assert serializer.data["location_lat"] == -6.3
    assert serializer.data["location_lon"] == 39.5


def test_detail_serializer_output(business_factory):
    business = business_factory(location=Point(39.1, -6.8))
    serializer = BusinessDetailSerializer(business)
    data = serializer.data
    assert data["name"] == business.name
    assert data["location"]["latitude"] == -6.8
    assert data["location"]["longitude"] == 39.1


def test_minimal_serializer_output(business_factory):
    business = business_factory()
    serializer = BusinessMinimalSerializer(business)
    data = serializer.data

    assert data["id"] == str(business.id)  # ✅ Convert UUID to string
    assert data["name"] == business.name
    assert data["slug"] == business.slug