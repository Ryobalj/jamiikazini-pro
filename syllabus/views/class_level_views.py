# syllabus/views/class_level_views.py

from rest_framework import viewsets
from syllabus.models.class_level import ClassLevel
from syllabus.serializers.class_level_serializer import ClassLevelSerializer
from syllabus.permissions import IsAdminOrReadOnly


class ClassLevelViewSet(viewsets.ModelViewSet):
    """
    CRUD kwa ClassLevel - kusoma (list/retrieve) kunaruhusiwa kwa
    mtumiaji yeyote aliyeingia (walimu wanahitaji hii kwa fomu za
    matokeo ya mtihani); kuhariri ni kwa Admin pekee.
    """
    queryset = ClassLevel.objects.all().order_by("order")
    serializer_class = ClassLevelSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)
        return qs