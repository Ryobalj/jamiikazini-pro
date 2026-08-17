# syllabus/services/lesson_notes_pdf_builder.py

from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from syllabus.services.pdf_base import PDFGenerator
from syllabus.services.data_models import LessonPlanData
from syllabus.services.lesson_diagrams import build_diagram
from syllabus.i18n import sw, en


class LessonNotesPDFBuilder:
    """
    Builds the standalone "Nukuu za Somo" (lesson notes) document — kept
    separate from the Andalio la Somo (lesson plan) itself, since a
    teacher downloading the lesson plan should receive the notes as their
    own document, not merged into the same pages.
    """

    def __init__(self, data: LessonPlanData, language: str = "sw"):
        self.data = data
        self.labels = sw.LESSON_PLAN if language == "sw" else en.LESSON_PLAN

        self.pdf = PDFGenerator(
            filename=f"NukuuZaSomo_{data.identification.class_level}.pdf",
            orientation="portrait",
            language=language,
        )

        self.text_style = ParagraphStyle(
            name="Normal", fontSize=9, leading=13, alignment=TA_LEFT
        )
        self.center_style = ParagraphStyle(
            name="Center", fontSize=10, alignment=TA_CENTER
        )

    def build(self) -> bytes:
        self._title()
        self._identification_section()
        self._notes_intro_section()
        self._notes_details_section()
        self._diagram_section()
        self._notes_illustrations_section()
        self._notes_daily_life_section()
        self._exercise_section()
        self._footer()
        return self.pdf.build()

    def _title(self):
        self.pdf.add_title(self.labels["lesson_notes"])
        self.pdf.add_spacer(6)

    def _identification_section(self):
        def cell(text):
            return Paragraph(str(text), self.text_style)

        def label(text):
            return Paragraph(f"<b>{text}:</b>", self.text_style)

        data = [
            [
                label(self.labels["school_name"]), cell(self.data.identification.school_name),
                label(self.labels["class_level"]), cell(self.data.identification.class_level)
            ],
            [
                label(self.labels["specific_competence"]), cell(self.data.subject_info.specific_competence),
                label(self.labels["main_activity"]), cell(self.data.subject_info.main_activity)
            ],
            [
                label(self.labels["specific_activity"]), cell(self.data.subject_info.specific_activity),
                "", ""
            ],
        ]

        table = Table(data, colWidths=[80, 155, 80, 145])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("SPAN", (1, 2), (3, 2)),
        ]))
        self.pdf.flowables.append(table)
        self.pdf.add_spacer(10)

    def _notes_intro_section(self):
        """Utangulizi — explains the concept of the topic."""
        intro = self.data.subject_info.lesson_notes_intro
        if not intro:
            return
        self.pdf.add_section(self.labels["notes_intro"])
        self.pdf.flowables.append(Paragraph(intro, self.text_style))
        self.pdf.add_spacer(6)

    def _notes_details_section(self):
        """Maelezo Zaidi — brief breakdown of types/parts, only if the
        topic actually has several (blank for simpler topics)."""
        details = self.data.subject_info.lesson_notes_details
        if not details:
            return
        self.pdf.add_section(self.labels["notes_details"])
        self.pdf.flowables.append(Paragraph(details, self.text_style))
        self.pdf.add_spacer(6)

    def _notes_illustrations_section(self):
        """Mifano — worked examples illustrating the concept itself."""
        illustrations = self.data.subject_info.lesson_notes_illustrations
        if not illustrations:
            return
        self.pdf.add_section(self.labels["notes_illustrations"])
        self.pdf.flowables.append(Paragraph(illustrations, self.text_style))
        self.pdf.add_spacer(6)

    def _notes_daily_life_section(self):
        """Matumizi Katika Maisha ya Kila Siku — real-life examples of
        where the concept shows up day-to-day."""
        daily_life = self.data.subject_info.lesson_notes_daily_life
        if not daily_life:
            return
        self.pdf.add_section(self.labels["notes_examples"])
        self.pdf.flowables.append(Paragraph(daily_life, self.text_style))
        self.pdf.add_spacer(8)

    def _diagram_section(self):
        drawing = build_diagram(self.data.subject_info.diagram_type)
        if drawing is None:
            return
        drawing.hAlign = "CENTER"
        self.pdf.flowables.append(drawing)
        self.pdf.add_spacer(8)

    def _exercise_section(self):
        questions = self.data.subject_info.exercise_questions
        if not questions:
            return
        self.pdf.add_section(self.labels["exercise"])
        for i, qa in enumerate(questions, start=1):
            question = qa.get("question", "")
            answer = qa.get("answer", "")
            self.pdf.flowables.append(Paragraph(f"{i}. {question}", self.text_style))
            self.pdf.flowables.append(
                Paragraph(f"<i>{self.labels['answer']}:</i> {answer}", self.text_style)
            )
        self.pdf.add_spacer(6)

    def _footer(self):
        footer_text = (
            f"{self.data.identification.school_name} - "
            f"{self.labels['lesson_notes']} - "
            f"{self.data.identification.teacher_name}"
        )
        self.pdf.set_footer(footer_text.upper())
