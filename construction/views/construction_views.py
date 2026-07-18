# construction/views/construction_views.py

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction as db_transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from accounts.permissions import IsIdentityVerified
from businesses.models.business import Business
from construction.models.construction_project import ConstructionProject, ConstructionProjectStatus
from construction.models.project_bid import ProjectBid, ProjectBidStatus
from construction.models.project_milestone import ProjectMilestone, ProjectMilestoneStatus
from construction.serializers import (
    ConstructionProjectSerializer,
    ConstructionProjectCreateSerializer,
    ProjectBidCreateSerializer,
    SelectBidSerializer,
    SubmitMilestoneSerializer,
    ApproveMilestoneSerializer,
)
from jamiiwallet.services.escrow_hold_service import open_hold, capture_from_hold, void_remaining


class ConstructionProjectViewSet(viewsets.ModelViewSet):
    """
    Mradi wa ujenzi wenye zabuni nyingi (multi-bid tender) na malipo ya awamu
    (milestones) kutoka HOLD moja ya jumla ya bei ya zabuni iliyoshinda.
    """
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        # IsIdentityVerified ni lango la MTEJA pekee (create) - mkandarasi
        # anatumia Business.is_verified badala ya NIDA ya kibinafsi.
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsIdentityVerified()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return ConstructionProjectCreateSerializer
        return ConstructionProjectSerializer

    def get_queryset(self):
        user = self.request.user
        if self.action == "open":
            return ConstructionProject.objects.filter(status=ConstructionProjectStatus.OPEN)
        return ConstructionProject.objects.filter(
            Q(client=user) | Q(contractor__owner=user) | Q(bids__contractor__owner=user)
        ).distinct().select_related("client", "contractor").prefetch_related("bids", "milestones")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        return Response(ConstructionProjectSerializer(project).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="open")
    def open(self, request):
        qs = self.get_queryset().select_related("client").order_by("-created_at")
        return Response(ConstructionProjectSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="bids")
    def submit_bid(self, request, pk=None):
        # self.get_object() ingetumia get_queryset(), ambayo haimjumuishi
        # mkandarasi asiyejulikana bado (hajawahi kutoa zabuni kwa mradi huu) -
        # hivyo tunatafuta mradi moja kwa moja, wazi kwa mkandarasi yeyote
        # aliyeautentike, mradi tu bado ni OPEN.
        try:
            project = ConstructionProject.objects.get(pk=pk)
        except ConstructionProject.DoesNotExist:
            raise NotFound("Mradi haupatikani.")
        if project.status != ConstructionProjectStatus.OPEN:
            raise ValidationError({"detail": "Mradi huu haupokei zabuni tena."})

        serializer = ProjectBidCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            business = Business.objects.get(pk=data["business_id"])
        except Business.DoesNotExist:
            raise NotFound("Biashara haipatikani.")
        if business.owner_id != request.user.id:
            raise PermissionDenied("Huwezi kutoa zabuni kwa biashara isiyo yako.")
        if not business.is_verified:
            raise PermissionDenied("Biashara yako bado haijathibitishwa - huwezi kutoa zabuni kwa sasa.")

        if ProjectBid.objects.filter(project=project, contractor=business).exists():
            raise ValidationError({"detail": "Tayari umetoa zabuni kwa mradi huu."})

        bid = ProjectBid.objects.create(
            project=project, contractor=business, price=data["price"],
            timeline_days=data["timeline_days"], notes=data.get("notes", ""),
        )
        return Response(ConstructionProjectSerializer(project).data | {"bid_id": str(bid.id)}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="select-bid")
    @db_transaction.atomic
    def select_bid(self, request, pk=None):
        serializer = SelectBidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = ConstructionProject.objects.select_for_update().get(pk=pk)
        if project.client_id != request.user.id:
            raise PermissionDenied("Huna ruhusa ya mradi huu.")
        if project.status != ConstructionProjectStatus.OPEN:
            raise ValidationError({"detail": "Mradi huu tayari umepewa mkandarasi au haupatikani."})

        try:
            bid = ProjectBid.objects.get(pk=serializer.validated_data["bid_id"], project=project, status=ProjectBidStatus.PENDING)
        except ProjectBid.DoesNotExist:
            raise NotFound("Zabuni hii haipatikani.")

        milestone_specs = serializer.validated_data["milestones"]
        try:
            amounts = [Decimal(str(m["amount"])) for m in milestone_specs]
        except (KeyError, InvalidOperation, TypeError):
            raise ValidationError({"milestones": "Kila hatua lazima iwe na 'name' na 'amount' sahihi."})
        if any(a <= 0 for a in amounts):
            raise ValidationError({"milestones": "Kiasi cha kila hatua lazima kiwe zaidi ya sifuri."})
        if sum(amounts) != bid.price:
            raise ValidationError({"milestones": "Jumla ya kiasi cha hatua zote lazima ilingane kikamilifu na bei ya zabuni."})

        if not hasattr(project.client, "wallet"):
            raise ValidationError({"detail": "Wallet ya mteja haipatikani."})

        try:
            eh = open_hold(
                project.client.wallet, bid.price, initiated_by=request.user,
                linked_object=project, idempotency_key=f"construction-award-{project.id}",
            )
        except DjangoValidationError:
            raise ValidationError({"detail": "Salio la mteja halitoshi kushikilia bei nzima ya zabuni hii."})

        for order, spec in enumerate(milestone_specs):
            ProjectMilestone.objects.create(
                project=project, name=spec["name"], amount=Decimal(str(spec["amount"])), order=order,
            )

        project.contractor = bid.contractor
        project.escrow_hold = eh
        project.status = ConstructionProjectStatus.AWARDED
        project.save(update_fields=["contractor", "escrow_hold", "status", "updated_at"])

        bid.status = ProjectBidStatus.ACCEPTED
        bid.save(update_fields=["status", "updated_at"])
        ProjectBid.objects.filter(project=project, status=ProjectBidStatus.PENDING).exclude(pk=bid.pk).update(
            status=ProjectBidStatus.REJECTED, updated_at=timezone.now()
        )

        return Response(ConstructionProjectSerializer(project).data)

    @action(detail=True, methods=["post"], url_path="submit-milestone")
    def submit_milestone(self, request, pk=None):
        project = self.get_object()
        if not (project.contractor_id and project.contractor.owner_id == request.user.id):
            raise PermissionDenied("Huna ruhusa ya mradi huu.")

        serializer = SubmitMilestoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            milestone = ProjectMilestone.objects.get(pk=serializer.validated_data["milestone_id"], project=project)
        except ProjectMilestone.DoesNotExist:
            raise NotFound("Hatua hii haipatikani.")
        if milestone.status != ProjectMilestoneStatus.PENDING:
            raise ValidationError({"detail": "Hatua hii tayari imewasilishwa au imelipwa."})

        milestone.status = ProjectMilestoneStatus.SUBMITTED
        milestone.submitted_at = timezone.now()
        if serializer.validated_data.get("evidence_image"):
            milestone.evidence_image = serializer.validated_data["evidence_image"]
        milestone.save(update_fields=["status", "submitted_at", "evidence_image", "updated_at"])

        return Response(ConstructionProjectSerializer(project).data)

    @action(detail=True, methods=["post"], url_path="approve-milestone")
    @db_transaction.atomic
    def approve_milestone(self, request, pk=None):
        project = ConstructionProject.objects.select_for_update().get(pk=pk)
        if project.client_id != request.user.id:
            raise PermissionDenied("Huna ruhusa ya mradi huu.")

        serializer = ApproveMilestoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            milestone = ProjectMilestone.objects.get(pk=serializer.validated_data["milestone_id"], project=project)
        except ProjectMilestone.DoesNotExist:
            raise NotFound("Hatua hii haipatikani.")
        if milestone.status != ProjectMilestoneStatus.SUBMITTED:
            raise ValidationError({"detail": "Hatua hii si SUBMITTED."})

        capture_from_hold(
            project.escrow_hold, milestone.amount, counterparty=project.contractor.owner,
            initiated_by=request.user, idempotency_key=f"construction-milestone-{milestone.id}",
        )

        milestone.status = ProjectMilestoneStatus.PAID
        milestone.approved_at = timezone.now()
        milestone.save(update_fields=["status", "approved_at", "updated_at"])

        if not project.milestones.exclude(status=ProjectMilestoneStatus.PAID).exists():
            project.status = ConstructionProjectStatus.COMPLETED
            project.save(update_fields=["status", "updated_at"])

        return Response(ConstructionProjectSerializer(project).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    @db_transaction.atomic
    def cancel(self, request, pk=None):
        project = ConstructionProject.objects.select_for_update().get(pk=pk)
        if project.client_id != request.user.id:
            raise PermissionDenied("Huna ruhusa ya mradi huu.")
        if project.status not in (ConstructionProjectStatus.OPEN, ConstructionProjectStatus.AWARDED):
            raise ValidationError({"detail": "Mradi huu hauwezi kughairiwa tena."})

        if project.escrow_hold:
            void_remaining(project.escrow_hold, initiated_by=request.user, idempotency_key=f"construction-cancel-{project.id}")

        project.status = ConstructionProjectStatus.CANCELLED
        project.save(update_fields=["status", "updated_at"])
        return Response(ConstructionProjectSerializer(project).data)
