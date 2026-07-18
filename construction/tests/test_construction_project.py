# construction/tests/test_construction_project.py

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from payments.models.currency import Currency
from construction.models.construction_project import ConstructionProject, ConstructionProjectStatus
from construction.models.project_bid import ProjectBid, ProjectBidStatus
from construction.models.project_milestone import ProjectMilestone, ProjectMilestoneStatus
from jamiiwallet.models.escrow_hold import EscrowHoldStatus

pytestmark = pytest.mark.django_db

PROJECTS_URL = "/api/v1/construction/projects/"


@pytest.fixture
def tzs(db):
    return Currency.objects.get_or_create(code="TZS")[0]


@pytest.fixture
def client_setup(user_factory, tzs):
    client_user = user_factory(role="CLIENT")
    client_user.is_identity_verified = True
    client_user.is_phone_verified = True
    client_user.save(update_fields=["is_identity_verified", "is_phone_verified"])
    client_user.wallet.balance = Decimal("10000000.00")
    client_user.wallet.save(update_fields=["balance"])
    return client_user


@pytest.fixture
def contractor_setup(business_factory, user_factory, tzs):
    owner = user_factory(role="PROVIDER")
    business = business_factory(owner=owner, is_verified=True)
    return {"owner": owner, "business": business}


def _milestones(total):
    half = (total / 2).quantize(Decimal("0.01"))
    return [
        {"name": "Msingi", "amount": str(half)},
        {"name": "Umaliziaji", "amount": str(total - half)},
    ]


class TestCreateProject:
    def test_requires_identity_verification(self, user_factory):
        unverified = user_factory(role="CLIENT")
        api = APIClient()
        api.force_authenticate(user=unverified)
        response = api.post(PROJECTS_URL, {"scope_description": "Jenga uzio"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verified_client_creates_project(self, client_setup):
        api = APIClient()
        api.force_authenticate(user=client_setup)
        response = api.post(PROJECTS_URL, {
            "scope_description": "Jenga uzio wa mita 50", "budget_ceiling": "2000000.00",
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["status"] == ConstructionProjectStatus.OPEN


class TestBidding:
    def _open_project(self, client_setup):
        return ConstructionProject.objects.create(client=client_setup, scope_description="Jenga uzio")

    def test_contractor_can_bid_on_open_project(self, client_setup, contractor_setup):
        project = self._open_project(client_setup)
        api = APIClient()
        api.force_authenticate(user=contractor_setup["owner"])
        response = api.post(f"{PROJECTS_URL}{project.id}/bids/", {
            "business_id": str(contractor_setup["business"].id), "price": "1000000.00", "timeline_days": 14,
        }, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert ProjectBid.objects.filter(project=project, contractor=contractor_setup["business"]).exists()

    def test_multiple_contractors_can_bid_and_client_compares(self, client_setup, contractor_setup, business_factory, user_factory):
        project = self._open_project(client_setup)
        other_owner = user_factory(role="PROVIDER")
        other_business = business_factory(owner=other_owner, is_verified=True)

        api = APIClient()
        api.force_authenticate(user=contractor_setup["owner"])
        api.post(f"{PROJECTS_URL}{project.id}/bids/", {
            "business_id": str(contractor_setup["business"].id), "price": "1000000.00", "timeline_days": 14,
        }, format="json")

        api.force_authenticate(user=other_owner)
        api.post(f"{PROJECTS_URL}{project.id}/bids/", {
            "business_id": str(other_business.id), "price": "900000.00", "timeline_days": 10,
        }, format="json")

        assert ProjectBid.objects.filter(project=project).count() == 2

    def test_unverified_contractor_cannot_bid(self, client_setup, business_factory, user_factory):
        project = self._open_project(client_setup)
        owner = user_factory(role="PROVIDER")
        business = business_factory(owner=owner, is_verified=False)
        api = APIClient()
        api.force_authenticate(user=owner)
        response = api.post(f"{PROJECTS_URL}{project.id}/bids/", {
            "business_id": str(business.id), "price": "1000000.00", "timeline_days": 14,
        }, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_bid_twice_on_same_project(self, client_setup, contractor_setup):
        project = self._open_project(client_setup)
        api = APIClient()
        api.force_authenticate(user=contractor_setup["owner"])
        first = api.post(f"{PROJECTS_URL}{project.id}/bids/", {
            "business_id": str(contractor_setup["business"].id), "price": "1000000.00", "timeline_days": 14,
        }, format="json")
        assert first.status_code == status.HTTP_201_CREATED
        second = api.post(f"{PROJECTS_URL}{project.id}/bids/", {
            "business_id": str(contractor_setup["business"].id), "price": "950000.00", "timeline_days": 12,
        }, format="json")
        assert second.status_code == status.HTTP_400_BAD_REQUEST


class TestSelectBid:
    def _project_with_bid(self, client_setup, contractor_setup, price="1000000.00"):
        project = ConstructionProject.objects.create(client=client_setup, scope_description="Jenga uzio")
        bid = ProjectBid.objects.create(
            project=project, contractor=contractor_setup["business"], price=Decimal(price), timeline_days=14,
        )
        return project, bid

    def test_select_bid_opens_full_hold_and_creates_milestones(self, client_setup, contractor_setup):
        project, bid = self._project_with_bid(client_setup, contractor_setup)
        api = APIClient()
        api.force_authenticate(user=client_setup)
        response = api.post(f"{PROJECTS_URL}{project.id}/select-bid/", {
            "bid_id": str(bid.id), "milestones": _milestones(Decimal("1000000.00")),
        }, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == ConstructionProjectStatus.AWARDED

        project.refresh_from_db()
        client_setup.wallet.refresh_from_db()
        assert project.contractor_id == contractor_setup["business"].id
        assert project.escrow_hold.total_held == Decimal("1000000.00")
        assert project.escrow_hold.status == EscrowHoldStatus.OPEN
        assert client_setup.wallet.held_balance == Decimal("1000000.00")
        assert ProjectMilestone.objects.filter(project=project).count() == 2

        bid.refresh_from_db()
        assert bid.status == ProjectBidStatus.ACCEPTED

    def test_selecting_one_bid_rejects_others(self, client_setup, contractor_setup, business_factory, user_factory):
        project, bid = self._project_with_bid(client_setup, contractor_setup)
        other_owner = user_factory(role="PROVIDER")
        other_business = business_factory(owner=other_owner, is_verified=True)
        losing_bid = ProjectBid.objects.create(project=project, contractor=other_business, price=Decimal("900000.00"), timeline_days=10)

        api = APIClient()
        api.force_authenticate(user=client_setup)
        api.post(f"{PROJECTS_URL}{project.id}/select-bid/", {
            "bid_id": str(bid.id), "milestones": _milestones(Decimal("1000000.00")),
        }, format="json")

        losing_bid.refresh_from_db()
        assert losing_bid.status == ProjectBidStatus.REJECTED

    def test_milestone_sum_must_equal_bid_price(self, client_setup, contractor_setup):
        project, bid = self._project_with_bid(client_setup, contractor_setup)
        api = APIClient()
        api.force_authenticate(user=client_setup)
        response = api.post(f"{PROJECTS_URL}{project.id}/select-bid/", {
            "bid_id": str(bid.id),
            "milestones": [{"name": "Msingi", "amount": "400000.00"}, {"name": "Umaliziaji", "amount": "400000.00"}],
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        project.refresh_from_db()
        assert project.status == ConstructionProjectStatus.OPEN

    def test_insufficient_balance_rejected(self, client_setup, contractor_setup):
        client_setup.wallet.balance = Decimal("100.00")
        client_setup.wallet.save(update_fields=["balance"])
        project, bid = self._project_with_bid(client_setup, contractor_setup)
        api = APIClient()
        api.force_authenticate(user=client_setup)
        response = api.post(f"{PROJECTS_URL}{project.id}/select-bid/", {
            "bid_id": str(bid.id), "milestones": _milestones(Decimal("1000000.00")),
        }, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestMilestoneFlow:
    def _awarded_project(self, client_setup, contractor_setup, price="900000.00"):
        project = ConstructionProject.objects.create(client=client_setup, scope_description="Jenga uzio")
        bid = ProjectBid.objects.create(project=project, contractor=contractor_setup["business"], price=Decimal(price), timeline_days=14)
        api = APIClient()
        api.force_authenticate(user=client_setup)
        api.post(f"{PROJECTS_URL}{project.id}/select-bid/", {
            "bid_id": str(bid.id), "milestones": _milestones(Decimal(price)),
        }, format="json")
        project.refresh_from_db()
        return project

    def test_contractor_submits_milestone(self, client_setup, contractor_setup):
        project = self._awarded_project(client_setup, contractor_setup)
        milestone = project.milestones.first()
        api = APIClient()
        api.force_authenticate(user=contractor_setup["owner"])
        response = api.post(f"{PROJECTS_URL}{project.id}/submit-milestone/", {"milestone_id": str(milestone.id)}, format="json")
        assert response.status_code == status.HTTP_200_OK
        milestone.refresh_from_db()
        assert milestone.status == ProjectMilestoneStatus.SUBMITTED

    def test_client_approving_milestone_captures_payment(self, client_setup, contractor_setup):
        project = self._awarded_project(client_setup, contractor_setup, price="900000.00")
        milestone = project.milestones.first()
        other_milestone = project.milestones.last()

        api = APIClient()
        api.force_authenticate(user=contractor_setup["owner"])
        api.post(f"{PROJECTS_URL}{project.id}/submit-milestone/", {"milestone_id": str(milestone.id)}, format="json")

        api.force_authenticate(user=client_setup)
        response = api.post(f"{PROJECTS_URL}{project.id}/approve-milestone/", {"milestone_id": str(milestone.id)}, format="json")
        assert response.status_code == status.HTTP_200_OK

        milestone.refresh_from_db()
        contractor_setup["owner"].wallet.refresh_from_db()
        assert milestone.status == ProjectMilestoneStatus.PAID
        assert contractor_setup["owner"].wallet.balance == milestone.amount

        project.refresh_from_db()
        assert project.status == ConstructionProjectStatus.AWARDED  # other_milestone still unpaid

    def test_all_milestones_paid_completes_project(self, client_setup, contractor_setup):
        project = self._awarded_project(client_setup, contractor_setup, price="900000.00")
        api = APIClient()

        for milestone in project.milestones.all():
            api.force_authenticate(user=contractor_setup["owner"])
            api.post(f"{PROJECTS_URL}{project.id}/submit-milestone/", {"milestone_id": str(milestone.id)}, format="json")
            api.force_authenticate(user=client_setup)
            api.post(f"{PROJECTS_URL}{project.id}/approve-milestone/", {"milestone_id": str(milestone.id)}, format="json")

        project.refresh_from_db()
        client_setup.wallet.refresh_from_db()
        assert project.status == ConstructionProjectStatus.COMPLETED
        assert client_setup.wallet.held_balance == Decimal("0.00")

    def test_stranger_cannot_approve_milestone(self, client_setup, contractor_setup, user_factory):
        project = self._awarded_project(client_setup, contractor_setup)
        milestone = project.milestones.first()
        stranger = user_factory(role="CLIENT")
        api = APIClient()
        api.force_authenticate(user=stranger)
        response = api.post(f"{PROJECTS_URL}{project.id}/approve-milestone/", {"milestone_id": str(milestone.id)}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCancel:
    def test_cancel_awarded_project_voids_remaining_hold(self, client_setup, contractor_setup):
        project = ConstructionProject.objects.create(client=client_setup, scope_description="Jenga uzio")
        bid = ProjectBid.objects.create(project=project, contractor=contractor_setup["business"], price=Decimal("900000.00"), timeline_days=14)
        api = APIClient()
        api.force_authenticate(user=client_setup)
        api.post(f"{PROJECTS_URL}{project.id}/select-bid/", {
            "bid_id": str(bid.id), "milestones": _milestones(Decimal("900000.00")),
        }, format="json")

        response = api.post(f"{PROJECTS_URL}{project.id}/cancel/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == ConstructionProjectStatus.CANCELLED

        client_setup.wallet.refresh_from_db()
        assert client_setup.wallet.held_balance == Decimal("0.00")
        assert client_setup.wallet.balance == Decimal("10000000.00")

    def test_cancel_partway_returns_only_unspent_funds(self, client_setup, contractor_setup):
        project = ConstructionProject.objects.create(client=client_setup, scope_description="Jenga uzio")
        bid = ProjectBid.objects.create(project=project, contractor=contractor_setup["business"], price=Decimal("900000.00"), timeline_days=14)
        api = APIClient()
        api.force_authenticate(user=client_setup)
        api.post(f"{PROJECTS_URL}{project.id}/select-bid/", {
            "bid_id": str(bid.id), "milestones": _milestones(Decimal("900000.00")),
        }, format="json")
        project.refresh_from_db()
        milestone = project.milestones.first()

        api.force_authenticate(user=contractor_setup["owner"])
        api.post(f"{PROJECTS_URL}{project.id}/submit-milestone/", {"milestone_id": str(milestone.id)}, format="json")
        api.force_authenticate(user=client_setup)
        api.post(f"{PROJECTS_URL}{project.id}/approve-milestone/", {"milestone_id": str(milestone.id)}, format="json")

        response = api.post(f"{PROJECTS_URL}{project.id}/cancel/")
        assert response.status_code == status.HTTP_200_OK

        client_setup.wallet.refresh_from_db()
        contractor_setup["owner"].wallet.refresh_from_db()
        assert client_setup.wallet.held_balance == Decimal("0.00")
        # 10,000,000 - 900,000 (full hold) + (900,000 - milestone.amount) voided back
        assert client_setup.wallet.balance == Decimal("10000000.00") - milestone.amount
        assert contractor_setup["owner"].wallet.balance == milestone.amount
