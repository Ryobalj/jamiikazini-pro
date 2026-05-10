# kiini/tests/test_institution_tier_serializer.py

import pytest
from kiini.models.institution_tier import InstitutionTier
from kiini.serializers.institution_tier_serializers import InstitutionTierSerializer


@pytest.mark.django_db
def test_serialize_institution_tier():
    tier = InstitutionTier.objects.create(
        name=InstitutionTier.TierChoices.MICRO,
        description="For micro-sized businesses"
    )
    serializer = InstitutionTierSerializer(tier)
    data = serializer.data

    assert data["id"] == str(tier.id)
    assert data["name"] == "MICRO"
    assert data["name_display"] == "Micro Enterprise"
    assert data["description"] == "For micro-sized businesses"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.django_db
def test_deserialize_valid_data():
    data = {
        "name": "SMALL",
        "description": "Small-sized businesses"
    }
    serializer = InstitutionTierSerializer(data=data)
    assert serializer.is_valid()
    instance = serializer.save()

    assert instance.name == "SMALL"
    assert instance.description == "Small-sized businesses"


@pytest.mark.django_db
def test_deserialize_invalid_enum_value():
    data = {
        "name": "INVALID",
        "description": "Invalid tier"
    }
    serializer = InstitutionTierSerializer(data=data)
    assert not serializer.is_valid()
    assert "name" in serializer.errors