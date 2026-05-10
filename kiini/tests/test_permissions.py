import pytest
from accounts.models import User
from kiini.models.institution import Institution
from django.contrib.gis.geos import Point

@pytest.mark.django_db
def test_user_belongs_to_institution():
    institution1 = Institution.objects.create(name="Shule A", domain="a.jamiikazini.com", location=Point(39.2, -6.8))
    user = User.objects.create_user(
        email="admin@a.com",
        password="admin123",
        full_name="Admin A",
        role="INSTITUTION_ADMIN"
    )
    user.institution = institution1
    user.save()

    assert user.institution.name == "Shule A"