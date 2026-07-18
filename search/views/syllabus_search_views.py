# search/views/syllabus_search_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from search.documents.syllabus_document import SyllabusSearchDocument
from search.utils.query_builder import build_syllabus_query


class SyllabusSearchAPIView(APIView):
    """
    Central syllabus search endpoint
    """

    # Public educational content.
    permission_classes = [permissions.AllowAny]

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
            syllabus_version = getattr(hit, "syllabus_version", None)
            main_competence = getattr(hit, "main_competence", None)
            specific_competence = getattr(hit, "specific_competence", None)
            learning_activity = getattr(hit, "learning_activity", None)
            data.append({
                "subject": getattr(hit, "subject", None),
                "class_level": getattr(hit, "class_level", None),
                "year": getattr(syllabus_version, "year", None) if syllabus_version else None,
                "main_competence": getattr(main_competence, "name", None) if main_competence else None,
                "specific_competence": getattr(specific_competence, "name", None) if specific_competence else None,
                "learning_activity": getattr(learning_activity, "name", None) if learning_activity else None,
                "specific_learning_activity": getattr(hit, "name", None),
                "method": getattr(hit, "method", None),
                "periods": getattr(hit, "periods", None),
            })

        return Response({
            "count": results.hits.total.value,
            "results": data
        })
