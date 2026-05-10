# search/views/syllabus_search_views.py

from rest_framework.views import APIView
from rest_framework.response import Response

from search.documents.syllabus_document import SyllabusSearchDocument
from search.utils.query_builder import build_syllabus_query


class SyllabusSearchAPIView(APIView):
    """
    Central syllabus search endpoint
    """

    def get(self, request):
        keyword = request.GET.get("q")
        class_level = request.GET.get("class_level")
        subject_code = request.GET.get("subject")
        year = request.GET.get("year")

        query = build_syllabus_query(
            keyword=keyword,
            class_level=class_level,
            subject_code=subject_code,
            year=year,
        )

        search = SyllabusSearchDocument.search().update_from_dict(query)
        results = search.execute()

        data = []
        for hit in results:
            data.append({
                "subject": hit.subject,
                "class_level": hit.class_level,
                "year": hit.syllabus_version.year,
                "main_competence": hit.main_competence.name,
                "specific_competence": hit.specific_competence.name,
                "learning_activity": hit.learning_activity.name,
                "specific_learning_activity": hit.name,
                "method": hit.method,
                "periods": hit.periods,
            })

        return Response({
            "count": results.hits.total.value,
            "results": data
        })
