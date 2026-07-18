# homepage/views/home_page_views.py

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import viewsets, permissions

from homepage.models.home_page import HomePage
from homepage.serializers.home_page_serializer import HomePageSerializer


class HomePageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve-only, scoped kwa mmiliki - inatumika hasa kama 'mzazi' wa
    nested routers za sections (/homepages/<id>/hero-sections/ n.k).
    Matumizi ya kawaida ya mmiliki ni kupitia MyHomePageView
    (/mine/<owner_type>/<owner_id>/); hii ipo kwa uthabiti wa URL tu.
    """
    queryset = HomePage.objects.all()
    serializer_class = HomePageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return super().get_queryset()

        from kiini.models.institution import Institution
        from businesses.models.business import Business

        inst_ids = Institution.objects.filter(owner=user).values_list('id', flat=True)
        biz_ids = Business.objects.filter(owner=user).values_list('id', flat=True)
        inst_ct = ContentType.objects.get_for_model(Institution)
        biz_ct = ContentType.objects.get_for_model(Business)

        return super().get_queryset().filter(
            Q(content_type=inst_ct, object_id__in=inst_ids)
            | Q(content_type=biz_ct, object_id__in=biz_ids)
        )
