# syllabus/services/exam_results_service.py

from decimal import Decimal

from syllabus.models.mark import Mark

GRADE_LETTERS = ["E", "D", "C", "B", "A"]


def grade_for_score(score, max_score):
    """Banda alama katika madaraja 5 sawa (E-A), kama ilivyo kwenye taarifa
    rasmi za TAMISEMI: kwa max_score=50, E:0-10, D:11-20, C:21-30, B:31-40,
    A:41-50."""
    if score is None or max_score <= 0:
        return None
    band = Decimal(max_score) / 5
    index = min(int((Decimal(score) - Decimal("0.01")) // band), 4) if score > 0 else 0
    return GRADE_LETTERS[max(0, index)]


def _rank_descending(values_by_id):
    """Standard competition ranking (1,2,2,4) - juu zaidi ndiyo namba 1.
    `values_by_id`: dict ya {id: Decimal/None}. Inarudisha dict {id: nafasi}."""
    ranked = sorted(
        [(k, v) for k, v in values_by_id.items() if v is not None],
        key=lambda kv: kv[1], reverse=True,
    )
    ranks = {}
    last_value = None
    last_rank = 0
    for position, (key, value) in enumerate(ranked, start=1):
        if value != last_value:
            last_rank = position
            last_value = value
        ranks[key] = last_rank
    return ranks


def compute_class_results(exam):
    """Kokotoa matokeo ya darasa zima kwa mtihani mmoja: alama/daraja/nafasi
    kwa kila somo, na jumla/wastani/daraja/nafasi kwa jumla. Inarudisha
    {"subjects": [Subject,...], "students": [{"student":..., "per_subject":
    {subject_id: {"score", "grade", "rank"}}, "total", "average",
    "overall_grade", "overall_rank"}, ...]}."""
    subjects = list(exam.subjects.all().order_by("name"))
    students = list(exam.workstation.students.filter(class_level=exam.class_level, is_active=True).order_by("full_name"))

    marks = Mark.objects.filter(exam=exam).select_related("student", "subject")
    marks_by_student_subject = {}
    for m in marks:
        marks_by_student_subject.setdefault(m.student_id, {})[m.subject_id] = m.score

    per_subject_ranks = {}
    for subject in subjects:
        scores_by_student = {
            student.id: marks_by_student_subject.get(student.id, {}).get(subject.id)
            for student in students
        }
        per_subject_ranks[subject.id] = _rank_descending(scores_by_student)

    totals_by_student = {}
    results = []
    for student in students:
        per_subject = {}
        total = Decimal(0)
        count = 0
        for subject in subjects:
            score = marks_by_student_subject.get(student.id, {}).get(subject.id)
            entry = {
                "score": score,
                "grade": grade_for_score(score, exam.max_score_per_subject) if score is not None else None,
                "rank": per_subject_ranks[subject.id].get(student.id),
            }
            per_subject[subject.id] = entry
            if score is not None:
                total += score
                count += 1
        average = (total / count) if count else None
        totals_by_student[student.id] = total if count else None
        results.append({
            "student": student,
            "per_subject": per_subject,
            "total": total if count else None,
            "average": average,
            "overall_grade": grade_for_score(average, exam.max_score_per_subject) if average is not None else None,
        })

    overall_ranks = _rank_descending(totals_by_student)
    for result in results:
        result["overall_rank"] = overall_ranks.get(result["student"].id)

    results.sort(key=lambda r: (r["overall_rank"] is None, r["overall_rank"] or 0))

    return {"subjects": subjects, "students": results}
