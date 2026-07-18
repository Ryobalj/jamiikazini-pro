# homepage/views/base.py

from django.http import Http404
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from homepage.models.home_page import HomePage


class HomePageScopedViewSet(viewsets.ModelViewSet):
    """
    Base ya ViewSets za sections zinazoning'inia moja kwa moja na HomePage
    (Hero, About, WhatWeDo, Faq, Testimonial). Usomaji ni wa umma (AllowAny)
    kama homepage imechapishwa; uandishi ni wa mmiliki wa homepage pekee.
    """
    homepage_kwarg = 'homepage_pk'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_homepage(self) -> HomePage:
        homepage_id = self.kwargs.get(self.homepage_kwarg)
        try:
            return HomePage.objects.select_related('content_type').get(pk=homepage_id)
        except HomePage.DoesNotExist:
            raise Http404('HomePage haikupatikana.')

    def get_queryset(self):
        homepage = self.get_homepage()
        qs = super().get_queryset().filter(homepage=homepage)
        if self.action in ['list', 'retrieve'] and not (
            self.request.user.is_authenticated and homepage.is_owned_by(self.request.user)
        ):
            qs = qs.filter(is_active=True)
        return qs

    def _check_owner(self, homepage):
        if not homepage.is_owned_by(self.request.user):
            raise PermissionDenied('Wewe si mmiliki wa homepage hii.')

    def perform_create(self, serializer):
        homepage = self.get_homepage()
        self._check_owner(homepage)
        serializer.save(homepage=homepage)

    def perform_update(self, serializer):
        self._check_owner(serializer.instance.homepage)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_owner(instance.homepage)
        instance.delete()


class ParentScopedViewSet(viewsets.ModelViewSet):
    """
    Base ya ViewSets za 'watoto wa watoto' (AboutImage chini ya AboutSection,
    WhatWeDoService/Image chini ya WhatWeDo) - ownership inapitiwa hadi
    kwenye homepage ya babu.
    """
    parent_model = None       # mfano: AboutSection
    parent_kwarg = None       # mfano: 'about_pk'
    parent_field = None       # jina la FK kwenye model ya mtoto, mfano 'about'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_parent(self):
        parent_id = self.kwargs.get(self.parent_kwarg)
        try:
            return self.parent_model.objects.select_related('homepage').get(pk=parent_id)
        except self.parent_model.DoesNotExist:
            raise Http404('Parent haikupatikana.')

    def get_queryset(self):
        parent = self.get_parent()
        qs = super().get_queryset().filter(**{self.parent_field: parent})
        if self.action in ['list', 'retrieve'] and not (
            self.request.user.is_authenticated and parent.homepage.is_owned_by(self.request.user)
        ):
            qs = qs.filter(is_active=True)
        return qs

    def _check_owner(self, parent):
        if not parent.homepage.is_owned_by(self.request.user):
            raise PermissionDenied('Wewe si mmiliki wa homepage hii.')

    def perform_create(self, serializer):
        parent = self.get_parent()
        self._check_owner(parent)
        serializer.save(**{self.parent_field: parent})

    def perform_update(self, serializer):
        parent = getattr(serializer.instance, self.parent_field)
        self._check_owner(parent)
        serializer.save()

    def perform_destroy(self, instance):
        parent = getattr(instance, self.parent_field)
        self._check_owner(parent)
        instance.delete()
