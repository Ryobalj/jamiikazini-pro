# syllabus/views/class_level_views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from syllabus.models.class_level import ClassLevel
from syllabus.serializers.class_level_serializer import ClassLevelSerializer


class ClassLevelViewSet(viewsets.ModelViewSet):
    """
    CRUD kwa ClassLevel – superuser tu anaweza kufanya operesheni zote.
    """
    queryset = ClassLevel.objects.all().order_by("order")
    serializer_class = ClassLevelSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)
        return qs