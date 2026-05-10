# businesses/tests/test_models/test_branch.py

import pytest
from django.utils import timezone
from businesses.models.branch import Branch
from businesses.models.business import Business
from kiini.models.institution import Institution
from accounts.models import User


@pytest.mark.django_db
def test_create_branch():
    institution = Institution.objects.create(name="Test Institution", domain="testorg")
    owner = User.objects.create_user(email="owner@example.com", password="testpass123", full_name="Owner", institution=institution)
    business = Business.objects.create(
        name="Test Business",
        owner=owner,
        institution=institution,
        description="Test business description",
        location="POINT(39.2 -6.8)",
        phone="255700000001",
        is_active=True,
    )

    branch = Branch.objects.create(
        business=business,
        name="Main Branch",
        phone="255700000002",
        location="POINT(39.2 -6.8)",
    )

    assert branch.id is not None
    assert branch.name == "Main Branch"
    assert branch.business == business


@pytest.mark.django_db
def test_branch_str():
    institution = Institution.objects.create(name="Another Institution", domain="anotherorg")
    owner = User.objects.create_user(email="admin@example.com", password="pass456", full_name="Admin", institution=institution)
    business = Business.objects.create(
        name="Business 2",
        owner=owner,
        institution=institution,
        description="Desc",
        location="POINT(39.3 -6.9)",
        phone="255700000003",
        is_active=True,
    )

    branch = Branch.objects.create(
        business=business,
        name="Branch 2",
        phone="255700000004",
        location="POINT(39.3 -6.9)",
    )

    assert str(branch) == f"Branch 2 - {business.name}"
