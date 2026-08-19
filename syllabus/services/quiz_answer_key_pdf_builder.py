# syllabus/services/quiz_answer_key_pdf_builder.py

from syllabus.services.quiz_paper_pdf_builder import build_quiz_pdf


def build_quiz_answer_key_pdf(paper, language: str = "sw") -> bytes:
    """Answer key / marking scheme for a GeneratedPaper - same renderer as
    the blank paper (see quiz_paper_pdf_builder.py), with answers and
    worked solutions shown."""
    return build_quiz_pdf(paper, language=language, show_answers=True)
