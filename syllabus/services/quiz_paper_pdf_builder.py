# syllabus/services/quiz_paper_pdf_builder.py

import random

from syllabus.models.question import Question
from syllabus.services.pdf_base import PDFGenerator

LABELS = {
    "sw": {
        "paper_title": "KARATASI YA MASWALI",
        "key_title": "MWONGOZO WA MAJIBU",
        "section_marks": "Alama",
        "instructions": "MAELEKEZO",
        "time": "Muda",
        "answer": "Jibu",
        "solution": "Mahesabu/Ufumbuzi",
        "marks_label": "alama",
    },
    "en": {
        "paper_title": "QUESTION PAPER",
        "key_title": "MARKING SCHEME",
        "section_marks": "Marks",
        "instructions": "INSTRUCTIONS",
        "time": "Time",
        "answer": "Answer",
        "solution": "Working/Solution",
        "marks_label": "marks",
    },
}


def _render_question(pdf, labels, index, gpq, show_answers, paper_seed):
    question = gpq.question
    line = f"{index}. ({gpq.marks} {labels['marks_label']}) {question.prompt}"
    pdf.add_paragraph(line)

    if question.passage_id and question.passage.text:
        pdf.add_paragraph(question.passage.text, small=True)

    if question.question_type == Question.QuestionType.MCQ and question.options:
        letters = "ABCDEFGH"
        opts = " &nbsp;&nbsp; ".join(
            f"{letters[i]}. {opt}" for i, opt in enumerate(question.options) if i < len(letters)
        )
        pdf.add_paragraph(opts, small=True)

    elif question.question_type == Question.QuestionType.MATCHING and question.options:
        pairs = question.options
        n = len(pairs)
        # Right-hand column must be scrambled relative to the left, or the
        # correct answer is trivially "1-A, 2-B, 3-C" every time. Shuffle is
        # deterministic per (paper, question) so the blank paper and the
        # answer key - rendered by separate, independent calls to this
        # function, possibly on separate downloads - always agree.
        rng = random.Random(f"{paper_seed}:{gpq.id}")
        order = list(range(n))
        rng.shuffle(order)
        left_text = "; ".join(f"{i + 1}. {pairs[i].get('left', '')}" for i in range(n))
        right_text = "; ".join(f"{chr(65 + k)}. {pairs[order[k]].get('right', '')}" for k in range(n))
        pdf.add_paragraph(f"A: {left_text}", small=True)
        pdf.add_paragraph(f"B: {right_text}", small=True)
        if show_answers:
            letter_for_left_index = {orig: chr(65 + k) for k, orig in enumerate(order)}
            mapping = ", ".join(f"{i + 1}-{letter_for_left_index[i]}" for i in range(n))
            pdf.add_paragraph(f"{labels['answer']}: {mapping}", small=True)
        pdf.add_spacer(6)
        return

    elif question.question_type == Question.QuestionType.FILL_BLANK and question.word_bank:
        pdf.add_paragraph(", ".join(question.word_bank), small=True)

    elif question.question_type == Question.QuestionType.MAP_DIAGRAM and question.diagram_image:
        try:
            from reportlab.platypus import Image
            pdf.flowables.append(Image(question.diagram_image.path, width=300, height=220))
        except Exception:
            pdf.add_paragraph("[Mchoro/Ramani]", small=True)

    if show_answers:
        pdf.add_paragraph(f"{labels['answer']}: {question.correct_answer}", small=True)
        if question.solution_steps:
            pdf.add_paragraph(f"{labels['solution']}: {question.solution_steps}", small=True)

    pdf.add_spacer(6)


def build_quiz_pdf(paper, language: str = "sw", show_answers: bool = False) -> bytes:
    """Renders a GeneratedPaper as either the blank question paper
    (show_answers=False) or the answer key / marking scheme
    (show_answers=True). Both share this one renderer so the two
    documents always stay structurally identical - only the workstation
    provided in `paper.workstation` and the format's own instructions
    differ per generation, never per-download.
    """
    labels = LABELS.get(language, LABELS["sw"])
    exam_format = paper.exam_format
    subject_version = paper.subject_version
    workstation = paper.workstation

    pdf = PDFGenerator(
        filename=f"{'Mwongozo' if show_answers else 'Karatasi'}_{subject_version.subject.name}.pdf",
        orientation="portrait",
        language=language,
    )
    pdf.set_header(workstation.school_name)
    pdf.add_paragraph(
        f"{exam_format.get_paper_type_display()} - {subject_version.subject.name} - {subject_version.class_level.name}",
        small=True,
    )
    if paper.year or paper.term:
        pdf.add_paragraph(f"{paper.year or ''} {'Muhula ' + str(paper.term) if paper.term else ''}".strip(), small=True)
    if exam_format.time_allowed_minutes:
        pdf.add_paragraph(f"{labels['time']}: {exam_format.time_allowed_minutes} min", small=True)

    pdf.add_title(labels["key_title"] if show_answers else labels["paper_title"])

    if exam_format.instructions and not show_answers:
        pdf.add_subsection(labels["instructions"])
        for line in exam_format.instructions.splitlines():
            if line.strip():
                pdf.add_paragraph(line, small=True)

    current_section = None
    for gpq in paper.paper_questions.select_related(
        "question", "question__passage"
    ).order_by("section_name", "order_in_section"):
        if gpq.section_name != current_section:
            current_section = gpq.section_name
            section_marks = sum(
                q.marks for q in paper.paper_questions.filter(section_name=current_section)
            )
            pdf.add_section(f"{current_section} ({labels['section_marks']} {section_marks})")
        _render_question(pdf, labels, gpq.order_in_section, gpq, show_answers, paper.seed)

    return pdf.build()
