# syllabus/services/quiz_generation_service.py

import random
import string
from typing import Dict, List, Optional

from django.db import transaction
from rest_framework.exceptions import ValidationError

from syllabus.models.exam_format import ExamFormat, ExamFormatSection, ExamFormatSlot
from syllabus.models.generated_paper import GeneratedPaper, GeneratedPaperQuestion
from syllabus.models.question import Question
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.teacher_workstation import TeacherWorkStation

# "Simplest question first, hardest last" - the sort key used to order
# each section's picks once selection is done.
DIFFICULTY_ORDER = {
    Question.Difficulty.EASY: 0,
    Question.Difficulty.MEDIUM: 1,
    Question.Difficulty.HARD: 2,
}


def generate_paper(
    *,
    exam_format: ExamFormat,
    subject_version: SubjectVersion,
    workstation: TeacherWorkStation,
    section_topic_ids: Optional[Dict[str, List[str]]] = None,
    title: str = "",
    year: Optional[int] = None,
    term: Optional[int] = None,
) -> GeneratedPaper:
    """Randomly assemble a paper from the question bank per exam_format's
    sections/slots, and persist the result as a GeneratedPaper. Within each
    section, picks are grouped by question_type (in the order that type's
    slot first appears in the section) and ordered easiest-first within
    each group - this lets the paper introduce each question-type group
    with its own instruction line ("Chagua herufi sahihi...", "Andika
    Kweli au Si Kweli...") instead of interleaving types. `section_topic_ids`
    optionally restricts each section's question pool to specific topics
    (LearningActivity ids), keyed by section id (str) - a section absent
    from the dict, or mapped to an empty list, draws from every topic in
    the subject. Raises ValidationError with a clear per-slot shortfall
    message if the bank doesn't have enough matching questions yet - this
    must fail loudly rather than silently generate a short or wrong paper,
    since the bank is authored incrementally.
    """
    sections = list(exam_format.sections.prefetch_related("slots").order_by("order"))
    if not sections:
        raise ValidationError({"exam_format": "Muundo huu wa mtihani hauna sehemu (sections) zilizowekwa."})

    base_qs = Question.objects.filter(
        is_active=True,
        learning_activity__specific_competence__main_competence__subject_version=subject_version,
    )
    section_topic_ids = section_topic_ids or {}

    shortfalls = []
    picks_by_section = {}

    for section in sections:
        section_qs = base_qs
        section_topics = section_topic_ids.get(str(section.id))
        if section_topics:
            section_qs = base_qs.filter(learning_activity_id__in=section_topics)

        picked_for_section = []
        already_picked_ids = set()
        # First-seen slot index per question_type, used below to keep
        # same-type questions grouped together in the rendered paper (each
        # group gets its own instruction line, e.g. "Chagua herufi sahihi
        # ...") instead of interleaving types within a section.
        type_group_order = {}
        for slot_index, slot in enumerate(section.slots.order_by("order")):
            type_group_order.setdefault(slot.question_type, slot_index)
            candidates = list(
                section_qs.filter(question_type=slot.question_type, difficulty=slot.difficulty)
                .exclude(id__in=already_picked_ids)
                .order_by("?")[: slot.count]
            )
            if len(candidates) < slot.count:
                shortfalls.append(
                    f"{section.name}: {slot.get_question_type_display()} ({slot.get_difficulty_display()}) - "
                    f"inahitajika {slot.count}, zilizopatikana {len(candidates)}"
                )
            for question in candidates:
                picked_for_section.append((question, slot.marks_per_item))
                already_picked_ids.add(question.id)
        picks_by_section[section] = (picked_for_section, type_group_order)

    if shortfalls:
        raise ValidationError({
            "detail": "Hazina ya maswali haina maswali ya kutosha kwa muundo huu wa mtihani:",
            "shortfalls": shortfalls,
        })

    seed = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))

    with transaction.atomic():
        paper = GeneratedPaper.objects.create(
            exam_format=exam_format,
            subject_version=subject_version,
            workstation=workstation,
            title=title,
            year=year,
            term=term,
            seed=seed,
        )
        for section, (picks, type_group_order) in picks_by_section.items():
            picks.sort(key=lambda pair: (
                type_group_order.get(pair[0].question_type, len(type_group_order)),
                DIFFICULTY_ORDER.get(pair[0].difficulty, 1),
            ))
            for order, (question, marks) in enumerate(picks, start=1):
                GeneratedPaperQuestion.objects.create(
                    generated_paper=paper,
                    question=question,
                    section_name=section.name,
                    order_in_section=order,
                    marks=marks,
                )

    return paper


def build_custom_exam_format(
    *,
    workstation: TeacherWorkStation,
    paper_type: str,
    custom_sections: list,
    title: str = "",
    time_allowed_minutes: Optional[int] = None,
    instructions: str = "",
):
    """Manual/'mwenyewe' paper-building path: persists exactly what the
    teacher specified (section names, each section's question-type/
    difficulty/count/marks slots, and per-section topic scope) as a real
    ExamFormat + Sections + Slots, `is_custom=True`. This is deliberately
    NOT a separate generation code path - it exists purely so
    generate_paper() can run against it unchanged, getting the same
    shortfall validation, type-grouping, and difficulty-ordering as any
    admin-curated template. Returns (exam_format, section_topic_ids) ready
    to hand straight to generate_paper().
    """
    with transaction.atomic():
        exam_format = ExamFormat.objects.create(
            name=title or f"Mwenyewe - {workstation.school_name} - {workstation.teacher.email}",
            paper_type=paper_type,
            time_allowed_minutes=time_allowed_minutes,
            instructions=instructions,
            is_custom=True,
            created_by_workstation=workstation,
        )
        section_topic_ids = {}
        for section_order, section_spec in enumerate(custom_sections, start=1):
            section = ExamFormatSection.objects.create(
                exam_format=exam_format,
                name=section_spec["name"],
                order=section_order,
            )
            for slot_order, slot_spec in enumerate(section_spec["slots"], start=1):
                ExamFormatSlot.objects.create(
                    section=section,
                    order=slot_order,
                    question_type=slot_spec["question_type"],
                    difficulty=slot_spec["difficulty"],
                    count=slot_spec["count"],
                    marks_per_item=slot_spec["marks_per_item"],
                )
            topic_ids = [str(t) for t in section_spec.get("topic_ids", [])]
            if topic_ids:
                section_topic_ids[str(section.id)] = topic_ids
        exam_format.recompute_total_marks()

    return exam_format, section_topic_ids
