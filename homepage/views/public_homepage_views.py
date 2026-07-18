# homepage/views/public_homepage_views.py

from django.http import Http404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from homepage.models.home_page import HomePage
from homepage.owner_resolution import resolve_owner, content_type_for
from homepage.serializers.public_serializer import PublicHomePageSerializer


class PublicHomePageView(APIView):
    """Homepage ya umma (bila auth) - inaonesha tu ikiwa is_published=True."""

    permission_classes = [AllowAny]

    def get(self, request, owner_type, owner_id):
        owner = resolve_owner(owner_type, owner_id)  # 404 wazi ikiwa owner haipo
        try:
            homepage = HomePage.objects.get(
                content_type=content_type_for(owner_type), object_id=owner.pk, is_published=True
            )
        except HomePage.DoesNotExist:
            raise Http404('Homepage haipo au bado haijachapishwa.')
        return Response(PublicHomePageSerializer(homepage, context={'request': request}).data)
