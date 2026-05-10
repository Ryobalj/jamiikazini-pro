# syllabus/services/pdf_base.py

"""
PDF Base Generator (Government Official Style)
Black & White only - No colors, no stripes, no fancy styling
"""

import io
from typing import Optional, List, Dict, Any
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import pdfencrypt
import logging

logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    Government official PDF generator - Black & White only.
    """
    def __init__(
        self, 
        filename: str = "document.pdf", 
        orientation: str = "portrait", 
        pagesize: str = "A4",
        encrypt: bool = True,
        compress: bool = True,
        metadata: Optional[Dict[str, str]] = None
    ):
        base = A4 if pagesize.upper() == "A4" else getattr(__import__('reportlab.lib.pagesizes'), pagesize, A4)
        self.pagesize = landscape(base) if orientation.lower() == "landscape" else portrait(base)
        self.filename = filename
        self.encrypt = encrypt
        self.compress = compress

        # Margins (government standard)
        self.margins = {
            'top': 20 * mm,
            'bottom': 20 * mm,
            'left': 25 * mm,
            'right': 20 * mm,
            'header': 10 * mm,
            'footer': 10 * mm,
        }

        # Styles
        self.styles = getSampleStyleSheet()
        self._setup_styles()

        # Content storage
        self.flowables: List = []

        # Metadata
        self.metadata = metadata or {
            'title': filename.replace('.pdf', ''),
            'author': 'Serikalini - Mfumo wa Mitaala',
            'subject': 'Azimio la Kazi',
            'keywords': 'elimu, mitaala, azimio',
            'creator': 'Wizara ya Elimu',
        }

        logger.debug(f"PDFGenerator initialized: {filename}")

    # ------------------- STYLES -------------------
    def _setup_styles(self) -> None:
        """Setup all paragraph styles - BLACK & WHITE ONLY."""
        
        # Base Normal style
        self.styles["Normal"].fontName = "Helvetica"
        self.styles["Normal"].fontSize = 10
        self.styles["Normal"].leading = 12
        self.styles["Normal"].spaceAfter = 6

        # Document Title - BLACK, CENTERED, BOLD
        self.styles.add(
            ParagraphStyle(
                name="DocTitle",
                parent=self.styles["Normal"],
                fontSize=16,
                leading=18,
                alignment=TA_CENTER,
                spaceAfter=12,
                spaceBefore=25,
                fontName="Helvetica-Bold",
            )
        )

        # Section Header - BLACK, BOLD
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Normal"],
                fontSize=13,
                leading=15,
                spaceBefore=15,
                spaceAfter=8,
                fontName="Helvetica-Bold",
            )
        )

        # Subsection Header - BLACK, BOLD
        self.styles.add(
            ParagraphStyle(
                name="SubsectionHeader",
                parent=self.styles["Normal"],
                fontSize=11,
                leading=13,
                spaceBefore=10,
                spaceAfter=5,
                fontName="Helvetica-Bold",
            )
        )

        # Small text (for tables and footnotes)
        self.styles.add(
            ParagraphStyle(
                name="Small",
                parent=self.styles["Normal"],
                fontSize=9,
                leading=11,
                spaceAfter=3,
            )
        )

        # Table Header - BOLD, CENTERED
        self.styles.add(
            ParagraphStyle(
                name="TableHeader",
                parent=self.styles["Small"],
                fontName="Helvetica-Bold",
                alignment=TA_CENTER,
            )
        )

        # Table Cell
        self.styles.add(
            ParagraphStyle(
                name="TableCell",
                parent=self.styles["Small"],
                alignment=TA_LEFT,
            )
        )

    # ------------------- CONTENT METHODS -------------------
    def add_title(self, text: str) -> None:
        """Add document title."""
        self.flowables.append(Paragraph(text, self.styles["DocTitle"]))
        self.flowables.append(Spacer(1, 8))
        logger.debug(f"Added title: {text[:50]}...")

    def add_section(self, text: str) -> None:
        """Add section header."""
        self.flowables.append(Paragraph(text, self.styles["SectionHeader"]))
        self.flowables.append(Spacer(1, 5))

    def add_subsection(self, text: str) -> None:
        """Add subsection header."""
        self.flowables.append(Paragraph(text, self.styles["SubsectionHeader"]))
        self.flowables.append(Spacer(1, 3))

    def add_paragraph(self, text: str, small: bool = False, style: Optional[str] = None) -> None:
        """Add paragraph text."""
        if style:
            para_style = self.styles.get(style, self.styles["Normal"])
        else:
            para_style = self.styles["Small"] if small else self.styles["Normal"]
        
        self.flowables.append(Paragraph(text, para_style))
        self.flowables.append(Spacer(1, 4 if small else 6))

    def add_spacer(self, height: int = 4) -> None:
        """Add vertical spacer."""
        self.flowables.append(Spacer(1, height))

    def add_page_break(self) -> None:
        """Add page break."""
        self.flowables.append(PageBreak())
        logger.debug("Added page break")

    # ------------------- TABLE METHODS -------------------
    def add_table(
        self, 
        data: List[List], 
        col_widths: Optional[List] = None,
        header_row: bool = True,
        style: Optional[TableStyle] = None,
    ) -> None:
        """
        Add table - BLACK & WHITE ONLY, NO STRIPES.
        """
        table = Table(data, colWidths=col_widths, repeatRows=1 if header_row else 0)
        
        # Default table style - SIMPLE BLACK & WHITE
        if style is None:
            style = TableStyle([
                # Grid - thin black lines
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                
                # Header styling - bold text only
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                
                # Cell styling
                ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                ("LEADING", (0, 1), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                
                # Left align for text columns, center for numbers
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
            ])
        
        table.setStyle(style)
        self.flowables.append(table)
        self.flowables.append(Spacer(1, 10))
        
        logger.debug(f"Added table with {len(data)} rows")

    # ------------------- PAGE NUMBERING CANVAS -------------------
    class NumberedCanvas(canvas.Canvas):
        """Custom canvas with page numbering."""
        def __init__(self, *args, **kwargs):
            self.header_text = kwargs.pop('header_text', '')
            self.footer_text = kwargs.pop('footer_text', '')
            super().__init__(*args, **kwargs)
            self._saved_pages = []

        def showPage(self):
            self._saved_pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            page_count = len(self._saved_pages)
            for state in self._saved_pages:
                self.__dict__.update(state)
                self._draw_header_footer(page_count)
                super().showPage()
            super().save()

        def _draw_header_footer(self, page_count: int):
            """Draw header, footer, and page numbers."""
            width, height = self._pagesize
            
            # Draw header if provided
            if self.header_text:
                self.setFont("Helvetica", 9)
                self.drawString(25, height - 20, self.header_text)
            
            # Draw footer if provided
            if self.footer_text:
                self.setFont("Helvetica", 8)
                self.drawString(25, 25, self.footer_text)
            
            # Draw page number
            self.setFont("Helvetica", 8)
            page_text = f"Uk. {self._pageNumber}/{page_count}"
            self.drawRightString(width - 25, 25, page_text)
            
            # Draw thin line at bottom
            self.line(25, 35, width - 25, 35)

    # ------------------- PDF BUILDING -------------------
    def build(self) -> bytes:
        """
        Build and return PDF as bytes.
        """
        logger.info(f"Building PDF: {self.filename}")
        
        buffer = io.BytesIO()

        # Setup encryption if enabled
        encryption = None
        if self.encrypt:
            encryption = pdfencrypt.StandardEncryption(
                userPassword="",
                ownerPassword="serikalini",
                canPrint=1,
                canModify=0,
                canCopy=0,
                canAnnotate=0,
                canFillForms=0,
                canAssemble=0,
                canPrintFull=0,
            )

        # Create document template
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.pagesize,
            leftMargin=self.margins["left"],
            rightMargin=self.margins["right"],
            topMargin=self.margins["top"],
            bottomMargin=self.margins["bottom"],
            encrypt=encryption,
            title=self.metadata.get('title', ''),
            author=self.metadata.get('author', ''),
            subject=self.metadata.get('subject', ''),
            keywords=self.metadata.get('keywords', ''),
            creator=self.metadata.get('creator', ''),
        )

        # Build document with custom canvas
        canvas_kwargs = {}
        if hasattr(self, 'header_text'):
            canvas_kwargs['header_text'] = self.header_text
        if hasattr(self, 'footer_text'):
            canvas_kwargs['footer_text'] = self.footer_text
            
        doc.build(self.flowables, canvasmaker=lambda *args, **kwargs: 
                 self.NumberedCanvas(*args, **kwargs, **canvas_kwargs))
        
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        
        logger.info(f"PDF built: {len(pdf_bytes)} bytes")
        return pdf_bytes

    def save_to_file(self, path: Optional[str] = None) -> str:
        """
        Save PDF to file.
        """
        filepath = path or self.filename
        pdf_bytes = self.build()
        
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)
        
        logger.info(f"PDF saved to: {filepath}")
        return filepath

    # ------------------- UTILITY METHODS -------------------
    def set_header(self, text: str) -> None:
        """Set document header text."""
        self.header_text = text

    def set_footer(self, text: str) -> None:
        """Set document footer text."""
        self.footer_text = text

    def __repr__(self) -> str:
        """String representation."""
        return f"PDFGenerator(filename={self.filename})"