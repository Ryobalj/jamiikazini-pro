def build_syllabus_query(
    keyword=None,
    class_level=None,
    subject_code=None,
    year=None,
):
    must = []
    filters = []

    if keyword:
        must.append({
            "multi_match": {
                "query": keyword,
                "fields": [
                    "name^5",
                    "learning_activity.name^4",
                    "specific_competence.name^4",
                    "main_competence.name^3",
                    "method",
                    "assessment_criteria",
                    "teaching_aids"
                ],
                "type": "best_fields"
            }
        })

    if class_level:
        filters.append({
            "term": {
                "class_level.name": class_level
            }
        })

    if subject_code:
        filters.append({
            "term": {
                "subject.code": subject_code
            }
        })

    if year:
        filters.append({
            "term": {
                "syllabus_version.year": year
            }
        })

    return {
        "query": {
            "bool": {
                "must": must or [{"match_all": {}}],
                "filter": filters
            }
        }
    }