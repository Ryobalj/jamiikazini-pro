# logistics/views/vehicle_views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from logistics.models import Vehicle, Driver
from logistics.models.vehicle_verification import VehicleVerification
from logistics.serializers.vehicle_serializer import VehicleSerializer, VehicleWriteSerializer
from logistics.permissions import IsProviderOwnerOrReadOnly
from gov_integration.helpers.verification import (
    verify_entity,
    vehicle_registration_authority_for,
    transport_license_authority_for,
)
from gov_integration.models.verification_request import VerificationRequest


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all().select_related('provider', 'active_driver').prefetch_related('drivers')
    permission_classes = [permissions.IsAuthenticated, IsProviderOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return VehicleWriteSerializer
        return VehicleSerializer

    def perform_create(self, serializer):
        # Automatically assign current user's transport_provider
        transport_provider = self.request.user.transport_providers.first()
        serializer.save(provider=transport_provider)

    def perform_update(self, serializer):
        # Prevent provider change on update
        serializer.save()

    @action(detail=True, methods=["post"], url_path="assign-driver")
    def assign_driver(self, request, pk=None):
        """
        Bonda dereva kwenye gari hili - dereva anabaki 'bonded' na gari hadi
        pale atakapoondolewa kwa uwazi kupitia release-driver (si kwa
        kubadilishwa kimyakimya). Dereva lazima awe wa mtoa-huduma huyu huyu.
        """
        vehicle = self.get_object()
        driver_id = request.data.get("driver_id")
        if not driver_id:
            raise ValidationError({"driver_id": "Chagua dereva wa kuunganisha na gari hili."})
        try:
            driver = vehicle.provider.drivers.get(pk=driver_id)
        except Driver.DoesNotExist:
            raise ValidationError({"driver_id": "Dereva huyu hapatikani kwenye akaunti yako."})

        if driver not in vehicle.drivers.all() and vehicle.drivers.count() >= 2:
            raise ValidationError({"driver_id": "Gari hili tayari lina madereva wawili walioruhusiwa."})

        vehicle.drivers.add(driver)
        vehicle.active_driver = driver
        vehicle.save(update_fields=["active_driver"])
        return Response(VehicleSerializer(vehicle, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="release-driver")
    def release_driver(self, request, pk=None):
        """
        Ondoa dereva (aliyeainishwa, au active_driver kama hakuna driver_id
        iliyotolewa) kutoka kwenye gari hili kwa uwazi - hii ndiyo hatua pekee
        inayovunja 'bonding' kati ya dereva na gari.
        """
        vehicle = self.get_object()
        driver_id = request.data.get("driver_id")
        driver = (
            vehicle.drivers.filter(pk=driver_id).first()
            if driver_id
            else vehicle.active_driver
        )
        if driver:
            vehicle.drivers.remove(driver)
            if vehicle.active_driver_id == driver.id:
                vehicle.active_driver = None
                vehicle.save(update_fields=["active_driver"])
        return Response(VehicleSerializer(vehicle, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        """
        Thibitisha gari hili dhidi ya TRA (usajili) na, kama lina namba ya
        kibali cha LATRA, dhidi ya LATRA pia - sawa na jinsi
        TransportProviderVerification inavyothibitisha MTU. Bila hii, namba na
        picha zilizopakiwa wakati wa usajili ni maelezo tu, si uthibitisho
        halisi.
        """
        vehicle = self.get_object()
        # Mamlaka ya uthibitisho ni tofauti kwa kila nchi (TRA/LATRA Tanzania,
        # NTSA Kenya, URSB Uganda, n.k.) - chaguo-msingi ni nchi ya mtoa-huduma
        # mwenyewe (TransportProvider.country_code), si "tz" iliyowekwa ngumu;
        # bado inaweza kupitwa wazi kwa request.data kama inahitajika.
        country_code = (request.data.get("country_code") or vehicle.provider.country_code or "tz").lower()
        verification, _ = VehicleVerification.objects.get_or_create(vehicle=vehicle)

        tra_payload = {"registration_number": vehicle.registration_number}
        tra_res = verify_entity(country_code, vehicle_registration_authority_for(country_code), tra_payload, request.user)
        tra_status = "VERIFIED" if tra_res.get("status") in ("success", "mock_success") else "FAILED"
        verification.tra_registration_verification = VerificationRequest.objects.create(
            user=request.user,
            institution=request.user.institution,
            country=country_code.upper(),
            payload=tra_payload,
            status=tra_status,
            response_data=tra_res,
        )

        latra_res = None
        if vehicle.latra_permit_number:
            latra_payload = {"latra_license_number": vehicle.latra_permit_number}
            latra_res = verify_entity(country_code, transport_license_authority_for(country_code), latra_payload, request.user)
            latra_status = "VERIFIED" if latra_res.get("status") in ("success", "mock_success") else "FAILED"
            verification.latra_permit_verification = VerificationRequest.objects.create(
                user=request.user,
                institution=request.user.institution,
                country=country_code.upper(),
                payload=latra_payload,
                status=latra_status,
                response_data=latra_res,
            )

        verification.save()
        verification.update_overall_status()

        return Response({
            "tra_registration": tra_res,
            "latra_permit": latra_res,
            "vehicle": VehicleSerializer(vehicle, context={"request": request}).data,
        })