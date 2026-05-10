import pytest
from decimal import Decimal
from businesses.models.service import Service
from businesses.serializers.service_serializer import ServiceSerializer
from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from accounts.models import User
from kiini.models.institution import Institution


@pytest.mark.django_db
class TestServiceSerializer:

    @pytest.fixture
    def sample_service(self):
        institution = Institution.objects.create(name="Sample Institution")
        owner = User.objects.create_user(email="owner@example.com", password="pass123", institution=institution)
        business = Business.objects.create(
            name="Test Business",
            institution=institution,
            owner=owner,
        )
        category = BusinessCategory.objects.create(name="Afya", slug="afya")
        return Service.objects.create(
            business=business,
            category=category,
            name="Huduma ya Massage",
            description="Huduma ya massage ya dakika 60.",
            price=Decimal("25000.00"),
            billing_type="per_hour",
            location_type="at_client",
            requires_booking=True,
            is_available=True,
            duration_minutes=60
        )

    def test_service_serializer_valid_data(self, sample_service):
        serializer = ServiceSerializer(instance=sample_service)
        data = serializer.data
        assert data["name"] == "Huduma ya Massage"
        assert data["price"] == "25000.00"
        assert data["billing_type_display"] == sample_service.get_billing_type_display()
        assert data["location_type_display"] == sample_service.get_location_type_display()
        assert data["duration_minutes"] == 60
        assert data["requires_booking"] is True
        assert data["is_available"] is True

    def test_service_serializer_invalid_duration(self, sample_service):
        service_data = {
            "business": sample_service.business.pk,
            "category": sample_service.category.pk,
            "name": "Huduma ya Haraka",
            "description": "",
            "price": "10000.00",
            "billing_type": "per_day",
            "location_type": "online",
            "requires_booking": False,
            "is_available": True,
            "duration_minutes": -15
        }
        serializer = ServiceSerializer(data=service_data)
        assert not serializer.is_valid()
        assert "duration_minutes" in serializer.errors

    def test_service_serializer_duration_optional(self, sample_service):
        service_data = {
            "business": sample_service.business.pk,
            "category": sample_service.category.pk,
            "name": "Huduma Fupi",
            "description": "",
            "price": "15000.00",
            "billing_type": "HOURLY",
            "location_type": "PROVIDER",
            "requires_booking": False,
            "is_available": True,
            "duration_minutes": None
        }
        serializer = ServiceSerializer(data=service_data)
        assert serializer.is_valid(), serializer.errors