# jamiikazini/syllabus/views/lesson_sentence_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from syllabus.models.lesson_sentence import LessonSentence
from syllabus.serializers.lesson_sentence_serializer import LessonSentenceSerializer


class LessonSentenceViewSet(viewsets.ModelViewSet):
    """
    Full CRUD kwa LessonSentence
    - Search
    - Filter
    - Random item endpoint
    - Superuser only
    """

    queryset = LessonSentence.objects.all()
    serializer_class = LessonSentenceSerializer
    permission_classes = [IsAdminUser]

    # -------------------------------
    # Filtering & Searching
    # -------------------------------
    filterset_fields = ["category", "is_active"]

    search_fields = [
        "teaching_sw",
        "learning_sw",
        "indicator_primary_sw",
        "indicator_secondary_sw",
        "teaching_en",
        "learning_en",
        "indicator_primary_en",
        "indicator_secondary_en",
        "reflection_sw",
        "reflection_comment_sw",
        "reflection_en",
        "reflection_comment_en",
    ]

    ordering_fields = ["created_at", "category"]
    ordering = ["category", "-created_at"]

    # --------------------------------
    # EXTRA ACTION: Random sentence
    # GET /lesson-sentences/random/?category=intro
    # --------------------------------
    @action(detail=False, methods=["get"], url_path="random")
    def random_sentence(self, request):
        category = request.query_params.get("category")

        if not category:
            return Response(
                {"detail": "Parameter 'category' inahitajika."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if category not in dict(LessonSentence.Category.choices):
            return Response(
                {"detail": "Category si sahihi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance = LessonSentence.pick_random(category)

        if not instance:
            return Response(
                {"detail": "Hakuna sentensi ya kundi hili."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)