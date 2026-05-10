# logistics/views/transport_provider_verification_views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from logistics.models.transport_provider_verification import TransportProviderVerification
from logistics.serializers.transport_provider_verification_serializer import TransportProviderVerificationSerializer
from gov_integration.helpers.verification import verify_entity


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

    def _save_verification_result(self, user, field_name, response):
        if response.get("status") == "success":
            request_id = response.get("data", {}).get("request_id")
            if request_id:
                tpv, _ = TransportProviderVerification.objects.get_or_create(
                    user=user,
                    institution=user.institution
                )
                setattr(tpv, f"{field_name}_id", request_id)
                tpv.update_overall_status()

    @action(detail=False, methods=['post'])
    def verify_all(self, request):
        """
        Trigger all relevant verification requests based on country_code and provided data.
        """
        user = request.user
        data = request.data
        country_code = data.get("country_code", "tz").lower()

        responses = {}

        if national_id := data.get("national_id_number"):
            payload = {"national_id_number": national_id}
            res = verify_entity(country_code, "nida", payload, user)
            self._save_verification_result(user, "nida_verification", res)
            responses["nida"] = res

        if license := data.get("driver_license_number"):
            payload = {"license_number": license}
            res = verify_entity(country_code, "driver", payload, user)
            self._save_verification_result(user, "driving_license_verification", res)
            responses["driver_license"] = res

        if biz := data.get("business_license_number"):
            payload = {"business_license_number": biz}
            res = verify_entity(country_code, "business", payload, user)
            self._save_verification_result(user, "vehicle_license_verification", res)
            responses["business_license"] = res

        if latra := data.get("latra_license_number"):
            payload = {"latra_license_number": latra}
            res = verify_entity(country_code, "transport", payload, user)
            self._save_verification_result(user, "latra_permit_verification", res)
            responses["latra"] = res

        return Response(responses, status=status.HTTP_200_OK)