# logistics/views/transport_provider_verification_views.py

from django.db import IntegrityError
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from logistics.models.transport_provider_verification import TransportProviderVerification
from logistics.serializers.transport_provider_verification_serializer import TransportProviderVerificationSerializer
from gov_integration.helpers.verification import (
    verify_entity,
    national_id_authority_for,
    driver_license_authority_for,
    business_license_authority_for,
    transport_license_authority_for,
)
from gov_integration.models.verification_request import VerificationRequest
from security.helpers.encryption import hash_data

DUPLICATE_DRIVER_LICENSE_MESSAGE = (
    "Namba hii ya leseni ya udereva tayari imetumika kuthibitisha akaunti nyingine. "
    "Kila leseni ya udereva inaruhusiwa kwenye akaunti moja tu."
)


class TransportProviderVerificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TransportProviderVerification.objects.select_related(
        'user', 'institution',
        'nida_verification',
        'driving_license_verification',
        'vehicle_license_verification',
        'latra_permit_verification'
    )
    serializer_class = TransportProviderVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "TRANSPORTER":
            return self.queryset.filter(user=user)
        elif user.role == "INSTITUTION_ADMIN":
            return self.queryset.filter(institution=user.institution)
        return self.queryset.none()

    def _save_verification_result(self, user, field_name, country_code, payload, response):
        """
        Andika VerificationRequest yenyewe kutokana na majibu ya verify_entity()
        (badala ya kutegemea request_id kutoka kwenye response - haipo kabisa
        kwenye mock_response(), na hata ingekuwepo, isingekuwa PK ya rekodi
        iliyokwisha kuwepo). Hii inafanya kazi sawa iwe jibu limetoka kwa gov
        API halisi au kwenye mock fallback ya dev/test.
        """
        result_status = "VERIFIED" if response.get("status") in ("success", "mock_success") else "FAILED"
        verification_request = VerificationRequest.objects.create(
            user=user,
            institution=user.institution,
            country=country_code.upper(),
            payload=payload,
            status=result_status,
            response_data=response,
        )
        tpv, _ = TransportProviderVerification.objects.get_or_create(
            user=user, institution=user.institution
        )
        setattr(tpv, field_name, verification_request)
        tpv.save()
        tpv.update_overall_status()

    @action(detail=False, methods=['post'])
    def verify_all(self, request):
        """
        Trigger all relevant verification requests based on country_code and provided data.
        """
        from kiini.models.institution import Institution

        user = request.user
        if not user.institution:
            institution, _ = Institution.objects.get_or_create(name="Jamiikazini User")
            user.institution = institution
            user.save(update_fields=["institution"])

        data = request.data
        country_code = data.get("country_code", "tz").lower()

        responses = {}

        if national_id := data.get("national_id_number"):
            payload = {"national_id_number": national_id}
            res = verify_entity(country_code, national_id_authority_for(country_code), payload, user)
            self._save_verification_result(user, "nida_verification", country_code, payload, res)
            responses["nida"] = res

        if license := data.get("driver_license_number"):
            # Leseni moja = dereva mmoja: hash ya kudumu inalinganishwa kabla
            # ya kuita mamlaka husika (sawa na National ID na leseni ya
            # biashara). Dereva huyu mwenyewe anaweza kuthibitisha tena.
            existing_tpv = TransportProviderVerification.objects.filter(user=user).first()
            license_hash = hash_data(license)
            duplicate_exists = TransportProviderVerification.objects.filter(
                driver_license_hash=license_hash
            ).exclude(pk=existing_tpv.pk if existing_tpv else None).exists()

            if duplicate_exists:
                responses["driver_license"] = {
                    "status": "failed", "verified": False,
                    "error": DUPLICATE_DRIVER_LICENSE_MESSAGE,
                }
            else:
                payload = {"license_number": license}
                res = verify_entity(country_code, driver_license_authority_for(country_code), payload, user)
                self._save_verification_result(user, "driving_license_verification", country_code, payload, res)
                if res.get("status") in ("success", "mock_success"):
                    tpv = TransportProviderVerification.objects.get(user=user, institution=user.institution)
                    tpv.driver_license_hash = license_hash
                    try:
                        tpv.save(update_fields=["driver_license_hash"])
                    except IntegrityError:
                        # Race guard: dereva mwingine amemaliza uthibitisho na
                        # leseni hii kati ya ukaguzi hapo juu na save() hii -
                        # geuza VerificationRequest iliyoundwa hivi punde kuwa
                        # FAILED ili overall_status isibaki ikisema VERIFIED.
                        res = {"status": "failed", "verified": False, "error": DUPLICATE_DRIVER_LICENSE_MESSAGE}
                        vr = tpv.driving_license_verification
                        if vr:
                            vr.status = "FAILED"
                            vr.response_data = res
                            vr.save(update_fields=["status", "response_data"])
                        tpv.update_overall_status()
                responses["driver_license"] = res

        if vehicle_license := data.get("vehicle_license_number"):
            payload = {"vehicle_license_number": vehicle_license}
            res = verify_entity(country_code, business_license_authority_for(country_code), payload, user)
            self._save_verification_result(user, "vehicle_license_verification", country_code, payload, res)
            responses["vehicle_license"] = res

        if latra := data.get("latra_license_number"):
            payload = {"latra_license_number": latra}
            res = verify_entity(country_code, transport_license_authority_for(country_code), payload, user)
            self._save_verification_result(user, "latra_permit_verification", country_code, payload, res)
            responses["latra"] = res

        return Response(responses, status=status.HTTP_200_OK)