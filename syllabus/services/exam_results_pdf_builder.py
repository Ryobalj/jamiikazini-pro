# syllabus/services/exam_results_pdf_builder.py

from reportlab.platypus import Table, TableStyle, Spacer, Paragraph
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from syllabus.services.pdf_base import PDFGenerator
from syllabus.services.exam_results_service import compute_class_results

# Subject names (e.g. "Demonstrate Mastery of Basic English Language
# Skills") are squeezed into a header cell only as wide as its 3
# score/grade/rank sub-columns combined. Plain strings in a reportlab
# Table don't wrap - they just overflow into the row below, which is
# exactly what happened here. Wrapping in a Paragraph makes the header
# grow downward instead.
_SUBJECT_HEADER_STYLE = ParagraphStyle(
    name="ExamSubjectHeader",
    fontName="Helvetica-Bold",
    fontSize=6.5,
    leading=7.5,
    alignment=TA_CENTER,
)

LABELS = {
    "sw": {
        "title": "MATOKEO YA MTIHANI",
        "na": "Na",
        "student": "Jina la Mwanafunzi",
        "score": "Alama",
        "grade": "Daraja",
        "rank": "Nafasi",
        "total": "Jumla",
        "average": "Wastani",
        "no_students": "Hakuna wanafunzi walioandikishwa kwenye darasa hili.",
    },
    "en": {
        "title": "EXAM RESULTS",
        "na": "No",
        "student": "Student Name",
        "score": "Score",
        "grade": "Grade",
        "rank": "Rank",
        "total": "Total",
        "average": "Average",
        "no_students": "No students have been registered for this class.",
    },
}


def _header(pdf, exam, labels):
    workstation = exam.workstation
    pdf.set_header(workstation.school_name)
    location_bits = [workstation.district]
    if workstation.region:
        location_bits.append(workstation.region)
    pdf.add_paragraph(" - ".join(location_bits), small=True)
    pdf.add_paragraph(
        f"{exam.name} - {exam.class_level.name} - {exam.get_term_display()} {exam.year}",
        small=True,
    )


def build_subject_result_pdf(exam, subject, language: str = "sw") -> bytes:
    """Karatasi ya matokeo ya somo moja tu (Nukuu ya Matokeo)."""
    labels = LABELS.get(language, LABELS["sw"])
    results = compute_class_results(exam)

    pdf = PDFGenerator(
        filename=f"Matokeo_{subject.name}_{exam.class_level.name}.pdf",
        orientation="portrait",
        language=language,
    )
    _header(pdf, exam, labels)
    pdf.add_title(f"{labels['title']} - {subject.name.upper()}")

    if not results["students"]:
        pdf.add_paragraph(labels["no_students"])
        return pdf.build()

    table_data = [[labels["na"], labels["student"], labels["score"], labels["grade"], labels["rank"]]]
    rows = sorted(
        results["students"],
        key=lambda r: (
            r["per_subject"].get(subject.id, {}).get("rank") is None,
            r["per_subject"].get(subject.id, {}).get("rank") or 0,
        ),
    )
    for i, r in enumerate(rows, start=1):
        entry = r["per_subject"].get(subject.id, {})
        table_data.append([
            str(i),
            r["student"].full_name,
            str(entry.get("score")) if entry.get("score") is not None else "-",
            entry.get("grade") or "-",
            str(entry.get("rank")) if entry.get("rank") is not None else "-",
        ])

    pdf.add_table(table_data)
    return pdf.build()


def build_class_report_pdf(exam, language: str = "sw") -> bytes:
    """Ripoti kamili ya darasa - masomo yote kwa kila mwanafunzi, ikiwa na
    jumla/wastani/daraja/nafasi ya jumla - mfano wa taarifa rasmi za
    TAMISEMI."""
    labels = LABELS.get(language, LABELS["sw"])
    results = compute_class_results(exam)

    pdf = PDFGenerator(
        filename=f"Matokeo_{exam.class_level.name}.pdf",
        orientation="landscape",
        language=language,
    )
    _header(pdf, exam, labels)
    pdf.add_title(f"{labels['title']} - {exam.class_level.name.upper()}")

    if not results["students"]:
        pdf.add_paragraph(labels["no_students"])
        return pdf.build()

    subjects = results["subjects"]

    header_row_1 = [labels["na"], labels["student"]]
    for subject in subjects:
        header_row_1.extend([Paragraph(subject.name, _SUBJECT_HEADER_STYLE), "", ""])
    header_row_1.extend([labels["total"], labels["average"], labels["grade"], labels["rank"]])

    header_row_2 = ["", ""]
    for _subject in subjects:
        header_row_2.extend([labels["score"], labels["grade"], labels["rank"]])
    header_row_2.extend(["", "", "", ""])

    table_data = [header_row_1, header_row_2]

    for i, r in enumerate(results["students"], start=1):
        row = [str(i), r["student"].full_name]
        for subject in subjects:
            entry = r["per_subject"].get(subject.id, {})
            row.append(str(entry.get("score")) if entry.get("score") is not None else "-")
            row.append(entry.get("grade") or "-")
            row.append(str(entry.get("rank")) if entry.get("rank") is not None else "-")
        row.append(str(r["total"]) if r["total"] is not None else "-")
        row.append(f"{r['average']:.2f}" if r["average"] is not None else "-")
        row.append(r["overall_grade"] or "-")
        row.append(str(r["overall_rank"]) if r["overall_rank"] is not None else "-")
        table_data.append(row)

    col_widths = [20, 90] + [22, 20, 20] * len(subjects) + [30, 30, 25, 25]
    col_widths = [w * 0.35 * mm for w in col_widths]

    table = Table(table_data, colWidths=col_widths, repeatRows=2)
    style_commands = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 1), 7),
        ("FONTSIZE", (0, 2), (-1, -1), 7),
        ("LEADING", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        # Merge each subject's 3 sub-columns under one subject-name header cell.
        ("SPAN", (0, 0), (0, 1)),
        ("SPAN", (1, 0), (1, 1)),
    ]
    col = 2
    for _subject in subjects:
        style_commands.append(("SPAN", (col, 0), (col + 2, 0)))
        col += 3
    for summary_col in range(col, col + 4):
        style_commands.append(("SPAN", (summary_col, 0), (summary_col, 1)))

    table.setStyle(TableStyle(style_commands))
    pdf.flowables.append(table)
    pdf.flowables.append(Spacer(1, 10))
    return pdf.build()
