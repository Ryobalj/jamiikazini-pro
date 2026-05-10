# businesses/tests/test_models/test_business.py

import pytest
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
def test_website_url_without_institution_domain(user, unique_institution):
    # Tumia domain unique lakini isiathiri url generation
    unique_institution.domain = f"nodomain-{unique_institution.id}.local"
    unique_institution.save()

    business = Business.objects.create(
        name="No Domain Biz",
        institution=unique_institution,
        owner=user,
    )

    expected = f"{slugify(business.name)}.{unique_institution.domain}"
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