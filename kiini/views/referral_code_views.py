# kiini/views/referral_code_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from kiini.models.referral_code import ReferralCode


class MyReferralCodeView(APIView):
    """Inarudisha (au kuunda) msimbo wa rufaa (dalali) wa mtumiaji aliyeingia."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        referral = ReferralCode.get_or_create_for_user(request.user)
        return Response({"code": referral.code})
