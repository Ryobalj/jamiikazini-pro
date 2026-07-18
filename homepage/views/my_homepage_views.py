# homepage/views/my_homepage_views.py

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from homepage.models.home_page import HomePage
from homepage.owner_resolution import resolve_owner
from homepage.serializers.home_page_serializer import HomePageSerializer


class MyHomePageView(APIView):
    """
    GET: pata (au tengeneza kama haipo) HomePage ya Institution/Business
    unayomiliki. PATCH: sasisha mipangilio yake (jina, rangi, mawasiliano).
    Mmiliki halisi (owner.owner == request.user) pekee.
    """
    permission_classes = [IsAuthenticated]

    def _get_homepage(self, request, owner_type, owner_id):
        owner = resolve_owner(owner_type, owner_id)
        if getattr(owner, 'owner_id', None) != request.user.id:
            raise PermissionDenied('Wewe si mmiliki wa Institution/Business hii.')
        return HomePage.get_or_create_for(owner)

    def get(self, request, owner_type, owner_id):
        homepage = self._get_homepage(request, owner_type, owner_id)
        return Response(HomePageSerializer(homepage).data)

    def patch(self, request, owner_type, owner_id):
        homepage = self._get_homepage(request, owner_type, owner_id)
        serializer = HomePageSerializer(homepage, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
