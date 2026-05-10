# syllabus/services/scheme_pdf_builder.py

from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
import logging
from typing import List, Optional
from datetime import datetime

from syllabus.services.pdf_base import PDFGenerator
from syllabus.services.data_models import SchemeData, ScheduleItem

logger = logging.getLogger(__name__)


class SchemePDFBuilder:
    """
    Government Official Scheme of Work PDF Builder - Black & White only
    Supports:
    1. Merged weeks format (Month: "Januari", Week: "3,4")
    2. 3-row merged holiday blocks with centered text
    3. Proper column alignment and formatting
    """
    def __init__(self, data: SchemeData, labels: Optional[dict] = None):
        self.data = data
        self.labels = labels or self._get_default_labels()
        
        filename = self._generate_filename()
        
        self.pdf = PDFGenerator(
            filename=filename,
            orientation="landscape",  # LANDSCAPE FOR WIDE TABLES
        )
        
        self._setup_styles()
        
        logger.info(f"SchemePDFBuilder initialized for: {data.subject_name}")

    def _get_default_labels(self) -> dict:
        """Get default Swahili labels."""
        return {
            "document_title": "AZIMIO LA KAZI",
            "council": "Halmashauri",
            "school_name": "Shule",
            "teacher_name": "Mwalimu",
            "class_level": "Darasa",
            "subject": "Somo",
            "year": "Mwaka",
            "term": "Muhula",
            "objectives": "Malengo",
            "holiday": "Likizo",
            "week": "Wiki",
            "periods": "Vipindi",
            "month": "Mwezi",
            "summary": "MUHTASARI",
            "exam_types": {
                "midterm": "Mitihani ya Robo ya Kwanza",
                "midannual": "Mitihani ya Nusu Muhula",
                "terminal": "Mitihani ya Mwisho wa Muhula",
                "annual": "Mitihani ya Mwisho wa Mwaka",
            },
            "headers": [
                "Umahiri Mkuu",
                "Umahiri Mahususi",
                "Shughuli za Ufundishaji",
                "Shughuli za Ujifunzaji",
                "Mwezi",
                "Wiki",
                "Vipindi",
                "Mbinu",
                "Marejeo",
                "Zana",
                "Vigezo vya Upimaji",
                "Maoni"
            ]
        }

    def _generate_filename(self) -> str:
        """Generate descriptive filename."""
        subject_clean = "".join(c for c in self.data.subject_name if c.isalnum() or c in (' ', '-', '_')).strip()
        class_clean = "".join(c for c in self.data.class_level_name if c.isalnum() or c in (' ', '-', '_')).strip()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        return f"Azimio_la_Kazi_{subject_clean}_{class_clean}_{timestamp}.pdf"

    def _setup_styles(self):
        """Setup custom paragraph styles - SIMPLE B&W."""
        # Holiday block exam row
        self.pdf.styles.add(
            ParagraphStyle(
                name="ExamRow",
                parent=self.pdf.styles["Small"],
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=12,
                spaceBefore=2,
                spaceAfter=2,
            )
        )
        
        # Holiday block holiday row
        self.pdf.styles.add(
            ParagraphStyle(
                name="HolidayRow",
                parent=self.pdf.styles["Small"],
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=12,
                spaceBefore=2,
                spaceAfter=2,
            )
        )
        
        # Holiday block date row
        self.pdf.styles.add(
            ParagraphStyle(
                name="DateRow",
                parent=self.pdf.styles["Small"],
                alignment=TA_CENTER,
                fontName="Helvetica-Oblique",
                fontSize=9,
                leading=11,
                spaceBefore=2,
                spaceAfter=2,
            )
        )
        
        # Style for period counts
        self.pdf.styles.add(
            ParagraphStyle(
                name="PeriodCount",
                parent=self.pdf.styles["Small"],
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                fontSize=9,
            )
        )
        
        # Style for merged month display
        self.pdf.styles.add(
            ParagraphStyle(
                name="MergedMonth",
                parent=self.pdf.styles["Small"],
                alignment=TA_CENTER,
                fontName="Helvetica",
                fontSize=9,
                leading=11,
            )
        )
        
        # Style for merged week numbers
        self.pdf.styles.add(
            ParagraphStyle(
                name="MergedWeek",
                parent=self.pdf.styles["Small"],
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=11,
            )
        )
        
        # Style for teaching activity cells
        self.pdf.styles.add(
            ParagraphStyle(
                name="TeachingCell",
                parent=self.pdf.styles["Small"],
                alignment=TA_LEFT,
                fontSize=8.5,
                leading=10,
            )
        )
        
        # Style for remarks
        self.pdf.styles.add(
            ParagraphStyle(
                name="RemarksCell",
                parent=self.pdf.styles["Small"],
                alignment=TA_LEFT,
                fontSize=8,
                leading=9.5,
            )
        )

    # -------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------
    def build(self) -> bytes:
        """
        Build complete Scheme of Work PDF with all features.
        """
        logger.info("Building complete Scheme of Work PDF...")
        
        try:
            self._build_header_page()
            self._build_objectives()
            self._build_period_summary()
            self._build_main_table()
            self._build_summary_footer()
            
            pdf_bytes = self.pdf.build()
            logger.info(f"PDF built successfully: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error building PDF: {str(e)}", exc_info=True)
            raise

    # -------------------------------------------------
    # HEADER PAGE
    # -------------------------------------------------
    def _build_header_page(self):
        """Build header page with school information."""
        self.pdf.add_title("AZIMIO LA KAZI")
        
        # School information table
        info_data = [
            ["Halmashauri:", self.data.council or "-"],
            ["Shule:", self.data.school_name or "-"],
            ["Mwalimu:", self.data.teacher_name or "-"],
            ["Darasa:", self.data.class_level_name or "-"],
            ["Somo:", self.data.subject_name or "-"],
            ["Mwaka:", self.data.year or "-"],
            ["Muhula:", self.data.term_display or self.data.term or "-"],
        ]
        
        info_table = Table(info_data, colWidths=[100, 350])
        info_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        
        self.pdf.flowables.append(info_table)
        self.pdf.add_spacer(15)

    # -------------------------------------------------
    # OBJECTIVES
    # -------------------------------------------------
    def _build_objectives(self):
        """Build objectives section."""
        self.pdf.add_section("MALENGO")
        
        objectives_list = self.data.objectives if hasattr(self.data, 'objectives') else []
        
        if objectives_list:
            for i, obj in enumerate(objectives_list, start=1):
                self.pdf.add_paragraph(f"{i}. {obj}", small=True)
        else:
            self.pdf.add_paragraph("Hakuna malengo maalum yaliyobainishwa.", small=True)
        
        self.pdf.add_spacer(12)

    # -------------------------------------------------
    # PERIOD SUMMARY
    # -------------------------------------------------
    def _build_period_summary(self):
        """Build period calculation summary."""
        if not hasattr(self.data, 'period_calculation'):
            return
        
        pc = self.data.period_calculation
        
        summary_data = [
            ["Jumla ya Vipindi Mtaalani:", str(pc.total_periods)],
            ["Vipindi kwa Wiki:", f"{pc.periods_per_week}"],
            ["Wiki Zinazohitajika:", f"{pc.required_weeks:.1f}"],
            ["Wiki Zilizopo:", str(pc.available_weeks)],
            ["Vipindi Vinavyopatikana:", str(pc.available_periods)],
            ["Tofauti ya Vipindi:", f"{pc.period_difference:+.1f}"],
            ["Vipindi Vilivyobaki kwa Wiki:", f"{pc.adjusted_periods_per_week:.1f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[150, 100])
        summary_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        
        self.pdf.flowables.append(summary_table)
        self.pdf.add_spacer(12)

    # -------------------------------------------------
    # MAIN SCHEME TABLE - COMPLETE WITH ALL FEATURES
    # -------------------------------------------------
    def _build_main_table(self):
        """Build main 12-column scheme table with all features."""
        headers = self.data.headers if hasattr(self.data, 'headers') else self.labels["headers"]
        
        # Start with header row
        table_data = [[Paragraph(h, self.pdf.styles["Small"]) for h in headers]]
        
        rows_on_current_page = 0
        max_rows_per_page = 35  # Increased for better spacing
        
        if hasattr(self.data, 'schedule_items') and self.data.schedule_items:
            for item in self.data.schedule_items:
                # Add page break if needed
                if rows_on_current_page >= max_rows_per_page:
                    self.pdf.flowables.append(PageBreak())
                    # Add header row on new page
                    table_data = [[Paragraph(h, self.pdf.styles["Small"]) for h in headers]]
                    rows_on_current_page = 0
                
                # Format row based on item type
                row_cells = self._format_table_row(item)
                table_data.append(row_cells)
                rows_on_current_page += 1
        
        # Column widths optimized for landscape with merged content
        col_widths = [
            70,   # Umahiri Mkuu (70)
            80,   # Umahiri Mahususi (80)
            110,  # Shughuli za Ufundishaji (110)
            110,  # Shughuli za Ujifunzaji (110)
            55,   # Mwezi (55)
            45,   # Wiki (45)
            35,   # Vipindi (35)
            65,   # Mbinu (65)
            75,   # Marejeo (75)
            75,   # Zana (75)
            70,   # Vigezo vya Upimaji (70)
            60,   # Maoni (60)
        ]
        
        # Create and style table
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        style_commands = [
            # Grid lines - simple black
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            
            # Header row styling
            ("BACKGROUND", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            
            # Column alignment
            ("ALIGN", (4, 1), (6, -1), "CENTER"),  # Month, Week, Periods centered
            ("ALIGN", (0, 1), (3, -1), "LEFT"),    # Competences left-aligned
            ("ALIGN", (7, 1), (10, -1), "LEFT"),   # Methodology, References, Teaching Aids, Assessment left
            ("ALIGN", (11, 1), (11, -1), "LEFT"),  # Remarks left-aligned
            
            # Cell padding for better readability
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
        ]
        
        # Apply styles to holiday blocks
        current_row = 1  # Start after header
        if hasattr(self.data, 'schedule_items'):
            for item in self.data.schedule_items:
                if self._is_holiday_block_row(item):
                    # Apply special styling to holiday block rows
                    style_commands.extend([
                        ("SPAN", (0, current_row), (3, current_row)),  # Merge first 4 columns
                        ("SPAN", (7, current_row), (10, current_row)), # Merge methodology through assessment
                        ("BACKGROUND", (0, current_row), (-1, current_row), colors.white),  # White background
                    ])
                current_row += 1
        
        table.setStyle(TableStyle(style_commands))
        self.pdf.flowables.append(table)
        self.pdf.add_spacer(10)

    def _format_table_row(self, item: ScheduleItem) -> List[Paragraph]:
        """Format a table row based on item type."""
        # Check if this is a holiday block row
        if self._is_holiday_block_row(item):
            return self._format_holiday_block_row(item)
        else:
            return self._format_teaching_row(item)
    
    def _is_holiday_block_row(self, item: ScheduleItem) -> bool:
        """Check if item is part of a holiday block."""
        if not item.student_activity:
            return False
        
        # Check for holiday/exam keywords
        holiday_keywords = ["MITIHANI", "LIKIZO", "Kuanzia tarehe"]
        return any(keyword in item.student_activity for keyword in holiday_keywords)
    
    def _format_holiday_block_row(self, item: ScheduleItem) -> List[Paragraph]:
        """Format 3-row holiday block with centered text."""
        # Determine which row of the block this is
        student_activity = item.student_activity or ""
        
        if "MITIHANI" in student_activity:
            style = self.pdf.styles["ExamRow"]
        elif "LIKIZO" in student_activity:
            style = self.pdf.styles["HolidayRow"]
        else:  # Date range row
            style = self.pdf.styles["DateRow"]
        
        # Get week display
        week_display = self._get_week_display(item)
        
        # For holiday blocks, student_activity goes in the 4th column (Shughuli za Ujifunzaji)
        # and is centered across merged cells
        centered_text = Paragraph(student_activity, style)
        
        return [
            Paragraph("", self.pdf.styles["TeachingCell"]),  # Umahiri Mkuu (empty, will be merged)
            Paragraph("", self.pdf.styles["TeachingCell"]),  # Umahiri Mahususi (empty, will be merged)
            Paragraph("", self.pdf.styles["TeachingCell"]),  # Shughuli za Ufundishaji (empty, will be merged)
            centered_text,                                   # Shughuli za Ujifunzaji (centered text)
            self._format_month_cell(item.month),
            self._format_week_cell(week_display),
            self._format_period_cell(item.periods),
            Paragraph("", self.pdf.styles["TeachingCell"]),  # Mbinu (empty, will be merged)
            Paragraph("", self.pdf.styles["TeachingCell"]),  # Marejeo (empty, will be merged)
            Paragraph("", self.pdf.styles["TeachingCell"]),  # Zana (empty, will be merged)
            Paragraph("", self.pdf.styles["TeachingCell"]),  # Vigezo vya Upimaji (empty, will be merged)
            self._format_remarks_cell(item.remarks),
        ]
    
    def _format_teaching_row(self, item: ScheduleItem) -> List[Paragraph]:
        """Format normal teaching activity row."""
        week_display = self._get_week_display(item)
        
        return [
            self._format_competence_cell(item.main_competence),
            self._format_competence_cell(item.specific_competence),
            self._format_activity_cell(item.learning_activity),
            self._format_activity_cell(item.student_activity),
            self._format_month_cell(item.month),
            self._format_week_cell(week_display),
            self._format_period_cell(item.periods),
            self._format_methodology_cell(item.methodology),
            self._format_references_cell(item.references),
            self._format_teaching_aids_cell(item.teaching_aids),
            self._format_assessment_cell(item.assessment_criteria),
            self._format_remarks_cell(item.remarks),
        ]

    # -------------------------------------------------
    # SPECIALIZED CELL FORMATTERS
    # -------------------------------------------------
    def _format_competence_cell(self, text: str) -> Paragraph:
        """Format competence cell (main or specific)."""
        if not text or text.strip() == "":
            text = "-"
        
        # Shorten very long competence names
        if len(text) > 100:
            text = text[:97] + "..."
        
        return Paragraph(text, self.pdf.styles["TeachingCell"])
    
    def _format_activity_cell(self, text: str) -> Paragraph:
        """Format activity cell (teaching or learning)."""
        if not text or text.strip() == "":
            text = "-"
        
        # Shorten very long activity names
        if len(text) > 120:
            text = text[:117] + "..."
        
        return Paragraph(text, self.pdf.styles["TeachingCell"])
    
    def _format_methodology_cell(self, text: str) -> Paragraph:
        """Format methodology cell."""
        if not text or text.strip() == "":
            text = "-"
        
        if len(text) > 80:
            text = text[:77] + "..."
        
        return Paragraph(text, self.pdf.styles["TeachingCell"])
    
    def _format_references_cell(self, text: Optional[str]) -> Paragraph:
        """Format references cell."""
        if not text or text.strip() == "":
            text = "-"
        
        if len(text) > 60:
            text = text[:57] + "..."
        
        return Paragraph(text, self.pdf.styles["TeachingCell"])
    
    def _format_teaching_aids_cell(self, text: Optional[str]) -> Paragraph:
        """Format teaching aids cell."""
        if not text or text.strip() == "":
            text = "-"
        
        if len(text) > 60:
            text = text[:57] + "..."
        
        return Paragraph(text, self.pdf.styles["TeachingCell"])
    
    def _format_assessment_cell(self, text: Optional[str]) -> Paragraph:
        """Format assessment criteria cell."""
        if not text or text.strip() == "":
            text = "-"
        
        if len(text) > 80:
            text = text[:77] + "..."
        
        return Paragraph(text, self.pdf.styles["TeachingCell"])
    
    def _format_remarks_cell(self, text: Optional[str]) -> Paragraph:
        """Format remarks cell."""
        if not text or text.strip() == "":
            text = "-"
        
        if len(text) > 50:
            text = text[:47] + "..."
        
        return Paragraph(text, self.pdf.styles["RemarksCell"])
    
    def _format_month_cell(self, text: str) -> Paragraph:
        """Format month cell (may contain merged months)."""
        if not text or text.strip() == "":
            text = "-"
        
        # Check if text contains comma (merged months)
        if "," in text:
            style = self.pdf.styles.get("MergedMonth", self.pdf.styles["Small"])
        else:
            style = self.pdf.styles["Small"]
        
        return Paragraph(str(text), style)
    
    def _format_week_cell(self, text: str) -> Paragraph:
        """Format week cell (comma-separated week numbers)."""
        if not text or text.strip() == "":
            text = "-"
        
        # Check if text contains comma (merged weeks)
        if "," in text:
            style = self.pdf.styles.get("MergedWeek", self.pdf.styles["Small"])
        else:
            style = self.pdf.styles["Small"]
        
        return Paragraph(str(text), style)
    
    def _format_period_cell(self, periods: int) -> Paragraph:
        """Format periods cell."""
        text = str(periods) if periods and periods > 0 else "0"
        style = self.pdf.styles.get("PeriodCount", self.pdf.styles["Small"])
        return Paragraph(text, style)
    
    def _get_week_display(self, item: ScheduleItem) -> str:
        """Get week numbers display for item."""
        # Check if we have weeks_display attribute
        if hasattr(item, 'weeks_display') and item.weeks_display:
            return item.weeks_display
        
        # Fallback: use week_number
        if hasattr(item, 'week_number') and item.week_number:
            return str(item.week_number)
        
        return "-"

    # -------------------------------------------------
    # SUMMARY AND FOOTER
    # -------------------------------------------------
    def _build_summary_footer(self):
        """Build summary footer with statistics."""
        if not hasattr(self.data, 'schedule_items') or not self.data.schedule_items:
            return
        
        # Calculate statistics
        teaching_weeks = set()
        teaching_rows = 0
        holiday_blocks = 0
        total_periods = 0
        
        for item in self.data.schedule_items:
            student_activity = item.student_activity or ""
            
            if "MITIHANI" in student_activity:
                holiday_blocks += 1
            elif item.periods > 0:
                teaching_rows += 1
                total_periods += item.periods
                
                # Count unique teaching weeks
                if hasattr(item, 'week_number') and item.week_number:
                    teaching_weeks.add(item.week_number)
        
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        summary_text = (
            f"MUHTASARI: Safu za mafunzo {teaching_rows} | "
            f"Wiki za mafunzo {len(teaching_weeks)} | "
            f"Vitalu vya likizo {holiday_blocks} | "
            f"Jumla ya vipindi {total_periods} | "
            f"Mwalimu: {self.data.teacher_name} | "
            f"Tarehe: {current_date}"
        )
        
        self.pdf.add_spacer(15)
        self.pdf.add_paragraph(summary_text, small=True)
        
        # Add school footer
        footer_text = f"{self.data.school_name} - {self.data.council}"
        self.pdf.set_footer(footer_text)