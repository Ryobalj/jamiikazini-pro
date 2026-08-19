# syllabus/services/quiz_paper_pdf_builder.py

import random

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether, Paragraph, Spacer, TableStyle

from syllabus.models.question import Question
from syllabus.services.pdf_base import PDFGenerator

# The council/school/subject/term/time block above "KARATASI YA MASWALI"
# is the paper's actual heading - it must be bold and centered like the
# title itself, not left-aligned plain text.
_HEADING_LINE_STYLE = ParagraphStyle(
    name="QuizHeadingLine", fontName="Helvetica-Bold", fontSize=11, leading=13,
    alignment=TA_CENTER, spaceAfter=2,
)
_NAME_DATE_STYLE = ParagraphStyle(
    name="QuizNameDateField", fontName="Helvetica-Bold", fontSize=10, leading=12,
)

LABELS = {
    "sw": {
        "paper_title": "KARATASI YA MASWALI",
        "key_title": "MWONGOZO WA MAJIBU",
        "section_marks": "Alama",
        "instructions": "MAELEKEZO",
        "time": "Muda",
        "answer": "Jibu",
        "solution": "Mahesabu/Ufumbuzi",
        "word_bank": "Chagua kutoka",
        "name_field": "Jina la Mwanafunzi",
        "date_field": "Tarehe",
    },
    "en": {
        "paper_title": "QUESTION PAPER",
        "key_title": "MARKING SCHEME",
        "section_marks": "Marks",
        "instructions": "INSTRUCTIONS",
        "time": "Time",
        "answer": "Answer",
        "solution": "Working/Solution",
        "word_bank": "Choose from",
        "name_field": "Student's Name",
        "date_field": "Date",
    },
}

# One instruction line introduces each question-type group within a
# section (e.g. all the MCQ questions together, then all the True/False
# questions together) - real Tanzanian exam papers always tell the pupil
# what to do before a block of same-type questions, never assume it's
# obvious from the question itself.
TYPE_INSTRUCTIONS = {
    "sw": {
        Question.QuestionType.MCQ: "Chagua herufi ya jibu sahihi kati ya A, B, C na D kisha andika herufi hiyo kwenye mabano uliyopewa.",
        Question.QuestionType.MATCHING: "Oanisha vipengele vya Sehemu A na Sehemu B.",
        Question.QuestionType.FILL_BLANK: "Jaza nafasi zilizoachwa wazi kwa kutumia maneno yaliyotolewa.",
        Question.QuestionType.SHORT_ANSWER: "Jibu maswali yafuatayo kwa ufupi.",
        Question.QuestionType.CALCULATION: "Onesha hesabu zako kikamilifu kisha andika jibu sahihi.",
        Question.QuestionType.SEQUENCING: "Panga hatua/vitu vifuatavyo kwa mpangilio sahihi.",
        Question.QuestionType.TRUE_FALSE: "Andika Kweli au Si Kweli kwa kila kauli ifuatayo.",
        Question.QuestionType.MAP_DIAGRAM: "Angalia mchoro/ramani kisha jibu maswali yafuatayo.",
        Question.QuestionType.COMPREHENSION: "Soma kifungu kifuatacho kisha jibu maswali yafuatayo.",
    },
    "en": {
        Question.QuestionType.MCQ: "Choose the letter of the correct answer among A, B, C and D and write it in the bracket provided.",
        Question.QuestionType.MATCHING: "Match the items in Column A with those in Column B.",
        Question.QuestionType.FILL_BLANK: "Fill in the blanks using the words provided.",
        Question.QuestionType.SHORT_ANSWER: "Answer the following questions briefly.",
        Question.QuestionType.CALCULATION: "Show your working clearly and write the correct answer.",
        Question.QuestionType.SEQUENCING: "Arrange the following steps/items in the correct order.",
        Question.QuestionType.TRUE_FALSE: "Write True or False for each of the following statements.",
        Question.QuestionType.MAP_DIAGRAM: "Study the map/diagram then answer the following questions.",
        Question.QuestionType.COMPREHENSION: "Read the following passage then answer the questions that follow.",
    },
}

GROUP_LETTERS = "abcdefgh"


def _marks_text(language: str, marks: int) -> str:
    """(Alama 1) in Kiswahili - word then number; (1 Mark) in English -
    number then word, pluralized. Always placed at the END of a question,
    never before it."""
    if language == "en":
        return f"({marks} Mark{'s' if marks != 1 else ''})"
    return f"(Alama {marks})"


def _add_centered_bold(pdf: PDFGenerator, text: str) -> None:
    pdf.flowables.append(Paragraph(text, _HEADING_LINE_STYLE))
    pdf.flowables.append(Spacer(1, 2))


def _add_name_date_row(pdf: PDFGenerator, labels: dict) -> None:
    """Placeholder line beneath the (capitalized, centered) title: the
    student's name starting from the left, the date at the right. Field
    labels are bold, same as every other heading on the paper."""
    avail_width = pdf.pagesize[0] - pdf.margins["left"] - pdf.margins["right"]
    left = Paragraph(f"{labels['name_field']}: " + "_" * 32, _NAME_DATE_STYLE)
    right = Paragraph(f"{labels['date_field']}: " + "_" * 14, _NAME_DATE_STYLE)
    data = [[left, right]]
    style = TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ])
    pdf.add_table(data, col_widths=[avail_width * 0.62, avail_width * 0.38], header_row=False, style=style)


def _render_question(pdf, labels, language, index, gpq, show_answers, paper_seed):
    question = gpq.question
    marks_text = _marks_text(language, gpq.marks)
    line = f"<b>{index}.</b> {question.prompt} {marks_text}"
    pdf.add_paragraph(line)

    if question.passage_id and question.passage.text:
        pdf.add_paragraph(question.passage.text, small=True)

    if question.question_type == Question.QuestionType.MCQ and question.options:
        letters = "ABCDEFGH"
        # Shuffled (deterministically, per paper+question) - authors
        # overwhelmingly write the correct choice as the first option, so
        # displaying options in authored order made the correct answer's
        # position trivially guessable (option A, almost every time).
        indices = list(range(min(len(question.options), len(letters))))
        random.Random(f"{paper_seed}:{gpq.id}:mcq").shuffle(indices)
        opts = " &nbsp;&nbsp; ".join(
            f"{letters[pos]}. {question.options[orig_i]}" for pos, orig_i in enumerate(indices)
        )
        correct_letter = ""
        if show_answers:
            for pos, orig_i in enumerate(indices):
                if question.options[orig_i].strip() == question.correct_answer.strip():
                    correct_letter = letters[pos]
                    break
        bracket = f"[ {correct_letter} ]" if show_answers else "[     ]"
        pdf.add_paragraph(f"{opts} &nbsp;&nbsp;&nbsp; {bracket}", small=True)

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
        # Shuffled (deterministically, per paper+question) so the correct
        # word isn't suspiciously first every time - a plain join() in
        # authored order tended to list the answer first, since authors
        # naturally write the correct word before the decoys.
        words = list(question.word_bank)
        random.Random(f"{paper_seed}:{gpq.id}:wb").shuffle(words)
        pdf.add_paragraph(f"{labels['word_bank']}: {', '.join(words)}", small=True)

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

    # The heading block - council, school, subject/class, term & year,
    # time - sits right where the title itself appears: bold and
    # centered, exactly like the title, not left-aligned plain text.
    if workstation.district:
        _add_centered_bold(pdf, workstation.district.upper())
    _add_centered_bold(pdf, workstation.school_name.upper())
    _add_centered_bold(pdf, (
        f"{exam_format.get_paper_type_display()} - {subject_version.subject.name} - "
        f"{subject_version.class_level.name}"
    ).upper())
    if paper.year or paper.term:
        term_word = "Term" if language == "en" else "Muhula"
        _add_centered_bold(pdf, f"{paper.year or ''} {term_word.upper() + ' ' + str(paper.term) if paper.term else ''}".strip())
    if exam_format.time_allowed_minutes:
        time_unit = "MIN" if language == "en" else "DAKIKA"
        _add_centered_bold(pdf, f"{labels['time'].upper()}: {exam_format.time_allowed_minutes} {time_unit}")

    pdf.add_title(labels["key_title"] if show_answers else labels["paper_title"])

    if not show_answers:
        _add_name_date_row(pdf, labels)

    if exam_format.instructions and not show_answers:
        pdf.add_subsection(labels["instructions"])
        for line in exam_format.instructions.splitlines():
            if line.strip():
                pdf.add_paragraph(line, small=True)

    type_instructions = TYPE_INSTRUCTIONS.get(language, TYPE_INSTRUCTIONS["sw"])
    current_section = None
    current_type = None
    group_letter_index = 0
    for gpq in paper.paper_questions.select_related(
        "question", "question__passage"
    ).order_by("section_name", "order_in_section"):
        if gpq.section_name != current_section:
            current_section = gpq.section_name
            current_type = None
            group_letter_index = 0
            section_marks = sum(
                q.marks for q in paper.paper_questions.filter(section_name=current_section)
            )
            pdf.add_section(f"{current_section} ({labels['section_marks']} {section_marks})")

        if gpq.question.question_type != current_type:
            current_type = gpq.question.question_type
            letter = GROUP_LETTERS[group_letter_index] if group_letter_index < len(GROUP_LETTERS) else str(group_letter_index + 1)
            group_letter_index += 1
            instruction = type_instructions.get(current_type, "")
            if instruction:
                pdf.add_paragraph(f"<b>({letter}) {instruction}</b>", small=True)

        # A question's own content (prompt, options, word bank, answer) must
        # never be split across a page break - wrap what it appends in a
        # single KeepTogether unit.
        start = len(pdf.flowables)
        _render_question(pdf, labels, language, gpq.order_in_section, gpq, show_answers, paper.seed)
        question_flowables = pdf.flowables[start:]
        del pdf.flowables[start:]
        pdf.flowables.append(KeepTogether(question_flowables))

    return pdf.build()
