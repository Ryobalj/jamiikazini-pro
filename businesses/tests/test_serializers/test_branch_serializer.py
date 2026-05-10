import pytest
from django.contrib.gis.geos import Point
from businesses.models.branch import Branch
from businesses.models.service import Service
from businesses.serializers.branch_serializer import BranchSerializer
from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from accounts.models import User
from kiini.models.institution import Institution


@pytest.mark.django_db
class TestBranchSerializer:

    @pytest.fixture
    def branch_with_services(self):
        institution = Institution.objects.create(name="Jamii Test Org")
        owner = User.objects.create_user(email="owner@example.com", password="test123", institution=institution)
        business = Business.objects.create(
            name="Jamii Electronics",
            owner=owner,
            institution=institution
        )
        category = BusinessCategory.objects.create(name="Huduma", slug="huduma")
        service1 = Service.objects.create(
            business=business,
            category=category,
            name="Service One",
            price=5000,
            billing_type="per_hour",
            location_type="online",
            requires_booking=False,
            is_available=True
        )
        service2 = Service.objects.create(
            business=business,
            category=category,
            name="Service Two",
            price=8000,
            billing_type="per_day",
            location_type="at_provider",
            requires_booking=True,
            is_available=True
        )

        branch = Branch.objects.create(
            business=business,
            name="Tawi la Posta",
            description="Huduma za haraka",
            
            location=Point(39.280556, -6.792354),  # longitude, latitude
            phone="+255712345678",
            email="posta@jamii.com",
            is_active=True,
        )
        branch.services.set([service1, service2])
        return branch

    def test_branch_serializer_output(self, branch_with_services):
        serializer = BranchSerializer(instance=branch_with_services)
        data = serializer.data

        assert data["name"] == "Tawi la Posta"
        assert data["business"] == branch_with_services.business.id
        assert data["phone"] == "+255712345678"
        assert data["email"] == "posta@jamii.com"
        assert data["is_active"] is True
        assert isinstance(data["services"], list)
        assert len(data["services"]) == 2
        assert data["business_name"] == branch_with_services.business.name
        assert data["services_count"] == 2

    def test_branch_serializer_create_valid(self, branch_with_services):
        payload = {
            "business": branch_with_services.business.id,
            "name": "Tawi Jipya",
            "description": "Maelezo mapya",
            "location": Point(39.21, -6.8),  # Tumia Point object, sio dict
            "phone": "+255789000111",
            "email": "jipya@jamii.com",
            "is_active": False,
            "services": [s.id for s in branch_with_services.services.all()],
        }
        serializer = BranchSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        branch = serializer.save()
        assert branch.name == "Tawi Jipya"
        assert branch.services.count() == 2