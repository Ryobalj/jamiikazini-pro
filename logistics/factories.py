# logistics/factories.py

import factory
from django.contrib.gis.geos import Point

# Institution & User from outside
from kiini.models.institution import Institution, InstitutionTier
from accounts.models import User

# Logistics-related models
from logistics.models.transport_provider import TransportProvider
from logistics.models.driver import Driver
from logistics.models.vehicle import Vehicle, VerificationStatus

# Business-related (category and business)
from businesses.models.category import BusinessCategory
from businesses.models.business import Business


# ---------- Institution Factories ----------
class InstitutionTierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InstitutionTier

    name = factory.Sequence(lambda n: f"Tier {n}")


class InstitutionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Institution

    name = factory.Sequence(lambda n: f"Institution {n}")
    domain = factory.Sequence(lambda n: f"institution{n}.example.com")
    email = factory.LazyAttribute(lambda o: f"contact@{o.domain}")
    phone = "255710000000"
    address = "Some address"
    location = factory.LazyFunction(lambda: Point(39.289, -6.823))
    tier = factory.SubFactory(InstitutionTierFactory)


# ---------- User Factory ----------
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    institution = factory.SubFactory(InstitutionFactory)
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True


# ---------- Business & Category ----------
class BusinessCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BusinessCategory

    name = factory.Sequence(lambda n: f"Category {n}")


class BusinessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Business

    institution = factory.SubFactory(InstitutionFactory)
    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Business {n}")
    category = factory.SubFactory(BusinessCategoryFactory)
    location = factory.LazyFunction(lambda: Point(39.28, -6.81))
    phone = "255700000001"
    email = factory.LazyAttribute(lambda o: f"{o.name.lower().replace(' ', '')}@example.com")
    website = "https://example.com"
    is_active = True


# ---------- TransportProvider ----------
class TransportProviderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TransportProvider

    user = factory.SubFactory(UserFactory)
    institution = factory.SubFactory(InstitutionFactory)
    provider_type = TransportProvider.ProviderType.INDIVIDUAL
    location = factory.LazyFunction(lambda: Point(39.27, -6.8))
    is_approved = False


# ---------- Driver ----------
class DriverFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Driver

    transport_provider = factory.SubFactory(TransportProviderFactory)
    full_name = factory.Faker('name')
    license_number = factory.Sequence(lambda n: f"A12345{n}")
    phone_number = "255700000002"
    is_verified = True
    is_active = True


# ---------- Vehicle ----------
class VehicleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vehicle

    provider = factory.SubFactory(TransportProviderFactory)
    vehicle_type = "pickup"
    registration_number = factory.Sequence(lambda n: f"T123{n}ABC")
    model_name = "Toyota Hilux"
    capacity_kg = 1000
    volume_cbm = 5.0
    is_active = True

    @factory.post_generation
    def drivers(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for driver in extracted:
                self.drivers.add(driver)
        else:
            driver = DriverFactory()
            self.drivers.add(driver)
            self.active_driver = driver
            self.save()

    verification_statuses = factory.LazyFunction(
        lambda: {
            "TRA": VerificationStatus.VERIFIED,
            "LATRA": VerificationStatus.PENDING,
            "POLICE": VerificationStatus.VERIFIED,
            "INSURANCE": VerificationStatus.FAILED
        }
    )