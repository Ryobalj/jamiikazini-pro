# syllabus/services/quiz_generation_service.py

import random
import string
from typing import List, Optional

from django.db import transaction
from rest_framework.exceptions import ValidationError

from syllabus.models.exam_format import ExamFormat
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
    topic_ids: Optional[List[str]] = None,
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
    Kweli au Si Kweli...") instead of interleaving types. Raises
    ValidationError with a clear per-slot shortfall message if the bank
    doesn't have enough matching questions yet - this must fail loudly
    rather than silently generate a short or wrong paper, since the bank
    is authored incrementally.
    """
    sections = list(exam_format.sections.prefetch_related("slots").order_by("order"))
    if not sections:
        raise ValidationError({"exam_format": "Muundo huu wa mtihani hauna sehemu (sections) zilizowekwa."})

    base_qs = Question.objects.filter(
        is_active=True,
        learning_activity__specific_competence__main_competence__subject_version=subject_version,
    )
    if topic_ids:
        base_qs = base_qs.filter(learning_activity_id__in=topic_ids)

    shortfalls = []
    picks_by_section = {}

    for section in sections:
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
                base_qs.filter(question_type=slot.question_type, difficulty=slot.difficulty)
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
