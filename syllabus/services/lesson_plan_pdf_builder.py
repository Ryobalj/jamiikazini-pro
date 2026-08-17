# syllabus/services/lesson_plan_pdf_builder.py

from reportlab.platypus import Table, TableStyle, Spacer, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from syllabus.services.pdf_base import PDFGenerator
from syllabus.services.data_models import LessonPlanData
from syllabus.i18n import sw, en


class LessonPlanPDFBuilder:
    """
    Builds a single-page Lesson Plan PDF (Portrait)
    Fully multilingual (labels and step headers)
    Supports footer and preview snippet
    """

    def __init__(self, data: LessonPlanData, language: str = "sw", preview: bool = False):
        self.data = data
        self.labels = sw.LESSON_PLAN if language == "sw" else en.LESSON_PLAN
        self.step_labels = self.labels["steps"]
        self.preview = preview  # If True, only show first N steps

        self.pdf = PDFGenerator(
            filename=f"LessonPlan_{data.identification.class_level}.pdf",
            orientation="portrait",
            language=language,
        )

        self.text_style = ParagraphStyle(
            name="Normal",
            fontSize=9,
            leading=11,
            alignment=TA_LEFT
        )

        self.center_style = ParagraphStyle(
            name="Center",
            fontSize=10,
            alignment=TA_CENTER
        )

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------
    def build(self):
        self._title()
        self._identification_section()
        self._students_section()
        self._lesson_information()
        self._lesson_steps()
        self._reflection_section()
        self._footer()
        return self.pdf.build()

    # ------------------------------------------------------------------
    # SECTIONS
    # ------------------------------------------------------------------
    def _title(self):
        self.pdf.add_title(self.labels["title"])
        self.pdf.add_spacer(6)

    def _identification_section(self):
        """
        SEHEMU YA I: TAARIFA ZA UTAMBULISHO (2x3 grid)
        """
        # Wrap every cell in a Paragraph so long values (e.g. a lengthy
        # main_competence) wrap within their column instead of overflowing
        # into the neighboring cell (plain strings in a reportlab Table do
        # not word-wrap). Label cells are bold, followed by a colon.
        def cell(text):
            return Paragraph(str(text), self.text_style)

        def label(text):
            return Paragraph(f"<b>{text}:</b>", self.text_style)

        data = [
            [
                label(self.labels["school_name"]), cell(self.data.identification.school_name),
                label(self.labels["teacher_name"]), cell(self.data.identification.teacher_name)
            ],
            [
                label(self.labels["main_competence"]), cell(self.data.identification.main_competence),
                label(self.labels["class_level"]), cell(self.data.identification.class_level)
            ],
            [
                label(self.labels["duration"]), cell(self.data.identification.time_range),
                label(self.labels["period"]), cell(self.data.identification.period)
            ],
            [
                label(self.labels["date"]), cell(self.data.identification.date),
                "", ""
            ],
        ]

        # Column widths sum to the page's real usable width (A4 minus
        # 25mm/20mm left/right margins, ~460pt) so this table spans edge
        # to edge instead of defaulting to reportlab's centered narrow
        # table when colWidths sum to less than the frame width.
        table = Table(data, colWidths=[80, 155, 80, 145])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        self.pdf.flowables.append(table)
        self.pdf.add_spacer(6)

    def _students_section(self):
        """
        SEHEMU YA II: IDADI YA WANAFUNZI
        """
        def header(text):
            return Paragraph(f"<b>{str(text).upper()}</b>", self.center_style)

        data = [
            [header(self.labels["registered"]), "", "", header(self.labels["attended"]), "", ""],
            [
                header(self.labels["boys"]), header(self.labels["girls"]), header(self.labels["total"]),
                header(self.labels["boys"]), header(self.labels["girls"]), header(self.labels["total"]),
            ],
            [
                str(self.data.registered_students.boys),
                str(self.data.registered_students.girls),
                str(self.data.registered_students.total),
                str(self.data.attended_students.boys),
                str(self.data.attended_students.girls),
                str(self.data.attended_students.total),
            ],
        ]
        # Sums to the same ~460pt usable width as the other tables in this
        # document, instead of 360pt (which left it centered with visible
        # margins on both sides).
        table = Table(data, colWidths=[77, 77, 77, 77, 76, 76])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("SPAN", (0, 0), (2, 0)),
            ("SPAN", (3, 0), (5, 0)),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        self.pdf.flowables.append(table)
        self.pdf.add_spacer(6)

    def _lesson_information(self):
        """
        SEHEMU YA III: TAARIFA ZA SOMO
        """
        info = [
            (self.labels["specific_competence"], self.data.subject_info.specific_competence),
            (self.labels["main_activity"], self.data.subject_info.main_activity),
            (self.labels["specific_activity"], self.data.subject_info.specific_activity),
            (self.labels["teaching_aids"], self.data.subject_info.teaching_aids),
            (self.labels["reference"], self.data.subject_info.references),
        ]

        for label, value in info:
            # teaching_aids/references are Postgres ArrayFields on
            # SpecificLearningActivity, so they may arrive as a list.
            if isinstance(value, (list, tuple)):
                value = ", ".join(str(v) for v in value if v)
            self.pdf.flowables.append(
                Paragraph(f"<b>{label}:</b> {value}", self.text_style)
            )
        self.pdf.add_spacer(6)

    def _lesson_steps(self):
        """
        SEHEMU YA IV: HATUA ZA SOMO
        Jedwali lenye columns 5:
        1. Hatua za Ufundishaji (fixed rows)
        2. Muda
        3. Shughuli za Ufundishaji
        4. Shughuli za Ujifunzaji
        5. Vigezo vya Upimaji
        """
    
        # -----------------------------
        # HEADER ROW (COLUMNS)
        # -----------------------------
        def header(text):
            return Paragraph(f"<b>{str(text).upper()}</b>", self.text_style)

        data = [[
            header(self.labels["step"]),               # Hatua za Ufundishaji
            header(self.labels["time"]),
            header(self.labels["teaching_activity"]),
            header(self.labels["learning_activity"]),
            header(self.labels["assessment"]),
        ]]
    
        # -----------------------------
        # FIXED ROW HEADERS (STEPS)
        # Order MUST match RuntimeBuilder
        # -----------------------------
        fixed_steps = self.labels["steps"]  # ["Utangulizi", "...", ...]
    
        # -----------------------------
        # MAP step_name -> LessonStep
        # -----------------------------
        step_map = {
            step.step_name: step
            for step in self.data.lesson_steps
        }
    
        # -----------------------------
        # BUILD ROWS
        # -----------------------------
        for step_label in fixed_steps:
            step = step_map.get(step_label)
    
            if step:
                # Convert timedelta to readable format (e.g., "5:00" or "5 min")
                duration = self._format_duration(step.duration)
                teaching = step.teaching_activity
                learning = step.learning_activity
                assessment = step.assessment_indicator
            else:
                duration = ""
                teaching = ""
                learning = ""
                assessment = ""
    
            # Wrap in Paragraph so long sentences wrap within the column
            # width instead of overflowing/overlapping neighboring cells
            # (plain strings in a reportlab Table do not word-wrap). The
            # step name acts as a row header, so it's capitalized+bold too.
            data.append([
                header(step_label),
                Paragraph(duration, self.text_style),
                Paragraph(teaching, self.text_style),
                Paragraph(learning, self.text_style),
                Paragraph(assessment, self.text_style),
            ])
    
        # -----------------------------
        # TABLE RENDERING
        # -----------------------------
        # Sums to ~460pt (page's real usable width), same proportions as
        # before but scaled down — the original [120,55,150,150,100]=575pt
        # exceeded the ~467pt usable width (A4 minus 25mm/20mm margins).
        table = Table(
            data,
            colWidths=[96, 44, 120, 120, 80]
        )
    
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (1, 1), (1, -1), "CENTER"),  # Muda column
        ]))
    
        self.pdf.flowables.append(table)
        self.pdf.add_spacer(6)

    def _format_duration(self, duration) -> str:
        """
        Format timedelta as a plain minute count so it can't be misread as
        a clock time (e.g. "5:00" looks like 5 o'clock, not 5 minutes).
        """
        if not duration:
            return ""

        try:
            minutes = int(duration.total_seconds()) // 60
            return f"{self.labels['minutes']} {minutes}"
        except:
            return str(duration)

    def _reflection_section(self):
        """
        SEHEMU YA V: MAONI NA TAFKURI
        """
        reflection = self.data.reflection
        if not reflection:
            return

        self.pdf.flowables.append(
            Paragraph(f"<b>{self.labels['reflection']}</b>", self.text_style)
        )

        items = [
            (self.labels["teaching_comment"], reflection.teaching_comment),
            (self.labels["assessment_comment"], reflection.assessment_comment),
            (self.labels["next_plan"], reflection.next_plan_comment),
        ]
        for label, value in items:
            if value and value.strip():
                self.pdf.flowables.append(
                    Paragraph(f"<b>{label}:</b> {value}", self.text_style)
                )

    def _footer(self):
        """
        Pin the school/teacher line to the bottom of every page next to the
        page number, instead of appending it as a body paragraph (which
        floats wherever the content flow happens to end).
        """
        footer_text = f"{self.data.identification.school_name} - {self.labels['title']} - {self.data.identification.teacher_name}"
        self.pdf.set_footer(footer_text.upper())

    # ------------------------------------------------------------------
    # ADDITIONAL HELPER METHODS
    # ------------------------------------------------------------------
    def create_preview_snippet(self):
        """
        Create a short preview for in-browser display (optional).
        """
        preview_flowables = []
        
        # Add title
        preview_flowables.append(Paragraph(f"<b>PREVIEW:</b> {self.labels['title']}", self.text_style))
        preview_flowables.append(Spacer(1, 6))
        
        # Add basic info
        preview_data = [
            [self.labels["school_name"], self.data.identification.school_name],
            [self.labels["teacher_name"], self.data.identification.teacher_name],
            [self.labels["class_level"], self.data.identification.class_level],
            [self.labels["date"], str(self.data.identification.date)],
        ]
        
        preview_table = Table(preview_data, colWidths=[80, 150])
        preview_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        
        preview_flowables.append(preview_table)
        preview_flowables.append(Spacer(1, 6))
        
        return preview_flowables