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
            orientation="portrait"
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
        data = [
            [
                self.labels["school_name"], self.data.identification.school_name,
                self.labels["teacher_name"], self.data.identification.teacher_name
            ],
            [
                self.labels["main_competence"], self.data.identification.main_competence,
                self.labels["class_level"], self.data.identification.class_level
            ],
            [
                self.labels["duration"], str(self.data.identification.duration),
                self.labels["period"], str(self.data.identification.period)
            ],
            [
                self.labels["date"], str(self.data.identification.date),
                "", ""
            ],
        ]

        table = Table(data, colWidths=[90, 150, 90, 120])
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
        data = [
            [self.labels["registered"], "", "", self.labels["attended"], "", ""],
            [
                self.labels["boys"], self.labels["girls"], self.labels["total"],
                self.labels["boys"], self.labels["girls"], self.labels["total"],
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
        table = Table(data, colWidths=[60] * 6)
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
            # 🔴 FIX: Change 'reference' to 'references' to match dataclass
            (self.labels.get("reference", "Marejeo"), self.data.subject_info.references),
        ]

        for label, value in info:
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
        data = [[
            self.labels["step"],               # Hatua za Ufundishaji
            self.labels["time"],
            self.labels["teaching_activity"],
            self.labels["learning_activity"],
            self.labels["assessment"],
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
    
            data.append([
                step_label,
                duration,
                teaching,
                learning,
                assessment,
            ])
    
        # -----------------------------
        # TABLE RENDERING
        # -----------------------------
        table = Table(
            data,
            colWidths=[120, 55, 150, 150, 100]
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
        Format timedelta to readable string.
        Example: timedelta(minutes=5) -> "5:00" or "5 min"
        """
        if not duration:
            return ""
        
        try:
            total_seconds = int(duration.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            
            if seconds == 0:
                return f"{minutes}:00"
            else:
                return f"{minutes}:{seconds:02d}"
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
        Footer with multilingual support
        """
        footer_text = f"{self.data.identification.school_name} - {self.labels['lesson_plan']} - {self.data.identification.teacher_name}"
        self.pdf.add_spacer(12)
        self.pdf.flowables.append(
            Paragraph(footer_text.upper(), self.center_style)
        )

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