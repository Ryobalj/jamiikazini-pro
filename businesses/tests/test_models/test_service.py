# businesses/tests/test_models/test_service.py

import pytest
from businesses.models.service import Service, BillingType, ServiceLocationType
from businesses.models.business import Business
from businesses.models.category import BusinessCategory
from kiini.models.institution import Institution
from accounts.models import User

pytestmark = pytest.mark.django_db

class TestServiceModel:
    def setup_method(self):
        self.institution = Institution.objects.create(name="Safari Hub", domain="safarihub")
        self.owner = User.objects.create_user(email="owner@safarihub.com", full_name="Safari Owner", password="password123", institution=self.institution)
        self.business = Business.objects.create(name="Safari Experts", slug="safariexperts", owner=self.owner, institution=self.institution)
        self.category = BusinessCategory.objects.create(name="Tours")

    def test_create_basic_service(self):
        service = Service.objects.create(
            business=self.business,
            category=self.category,
            name="Wildlife Safari",
            description="Explore the savannah",
            price=150000,
            billing_type=BillingType.DAILY,
            location_type=ServiceLocationType.CLIENT_LOCATION,
            requires_booking=True,
            is_available=True,
            duration_minutes=240
        )

        assert service.name == "Wildlife Safari"
        assert service.business == self.business
        assert service.category == self.category
        assert service.billing_type == BillingType.DAILY
        assert service.location_type == ServiceLocationType.CLIENT_LOCATION
        assert service.requires_booking is True
        assert str(service) == f"Wildlife Safari - {self.business.name}"

    def test_service_without_optional_fields(self):
        service = Service.objects.create(
            business=self.business,
            name="Translation Service",
            price=25000
        )
        assert service.is_available is True
        assert service.duration_minutes is None
        assert service.category is None
        assert str(service) == f"Translation Service - {self.business.name}"