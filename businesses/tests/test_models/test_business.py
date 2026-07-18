# businesses/tests/test_models/test_business.py

import pytest
from django.conf import settings
from django.utils.text import slugify
from businesses.models.business import Business


@pytest.mark.django_db
def test_business_creation(user, unique_institution):
    Business.objects.all().delete()  # Cleanup to avoid slug conflicts

    business = Business.objects.create(
        name="Biashara Yetu",
        institution=unique_institution,
        owner=user,
        phone="+255700000000",
        email="biashara@example.com",
    )

    assert business.name == "Biashara Yetu"
    assert business.institution == unique_institution
    assert business.owner == user
    assert business.slug == slugify("Biashara Yetu")
    assert not business.is_verified
    assert str(business) == "Biashara Yetu"

@pytest.mark.django_db
def test_website_url_uses_own_domain_field(user, unique_institution):
    business = Business.objects.create(
        name="No Domain Biz",
        institution=unique_institution,
        owner=user,
    )

    expected = f"https://{business.domain}.{settings.CENTRAL_DOMAIN}"
    assert business.website_url == expected

@pytest.mark.django_db
def test_slug_auto_generation(user, unique_institution):
    business = Business.objects.create(
        name="Kitu Kipya",
        institution=unique_institution,
        owner=user,
    )

    expected_slug = slugify("Kitu Kipya")
    assert business.slug == expected_slug

@pytest.mark.django_db
def test_domain_auto_populated_from_slug(user, unique_institution):
    business = Business.objects.create(
        name="Domain Auto Test",
        institution=unique_institution,
        owner=user,
    )
    assert business.domain == business.slug == slugify("Domain Auto Test")

@pytest.mark.django_db
def test_slug_collision_gets_auto_suffix(user, unique_institution):
    first = Business.objects.create(name="Duka Moja", institution=unique_institution, owner=user)
    second = Business.objects.create(name="Duka Moja", institution=unique_institution, owner=user)

    assert first.slug == slugify("Duka Moja")
    assert second.slug == f"{slugify('Duka Moja')}-2"
    assert second.domain == second.slug
    # No IntegrityError raised - both saved successfully with distinct slugs/domains.
    assert Business.objects.filter(name="Duka Moja").count() == 2