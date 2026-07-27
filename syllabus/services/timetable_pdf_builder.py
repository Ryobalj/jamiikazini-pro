# syllabus/services/timetable_pdf_builder.py

from syllabus.services.pdf_base import PDFGenerator
from syllabus.models.timetable import TimeTable

DAY_LABELS = {
    "sw": {1: "JUMATATU", 2: "JUMANNE", 3: "JUMATANO", 4: "ALHAMISI", 5: "IJUMAA", 6: "JUMAMOSI"},
    "en": {1: "MONDAY", 2: "TUESDAY", 3: "WEDNESDAY", 4: "THURSDAY", 5: "FRIDAY", 6: "SATURDAY"},
}

LABELS = {
    "sw": {
        "title": "RATIBA YA VIPINDI",
        "class_col": "DARASA",
        "time_row": "MUDA",
        "no_entries": "Hakuna vipindi vilivyowekwa bado.",
    },
    "en": {
        "title": "TIMETABLE",
        "class_col": "CLASS",
        "time_row": "TIME",
        "no_entries": "No periods have been set up yet.",
    },
}


def _time_str(t):
    return t.strftime("%H:%M") if t else ""


def build_teacher_timetable_pdf(workstation, language: str = "sw") -> bytes:
    """Personal weekly timetable grid for one teacher, grouped by day then
    class - mirrors the layout of real school 'ratiba ya vipindi' sheets
    (day -> one row per class the teacher takes that day -> period columns).
    """
    labels = LABELS.get(language, LABELS["sw"])
    day_labels = DAY_LABELS.get(language, DAY_LABELS["sw"])

    rows = list(
        TimeTable.objects.filter(
            workstation=workstation,
            day_of_week__isnull=False,
            period__isnull=False,
        )
        .select_related("subject_version__subject", "subject_version__class_level")
        .order_by("day_of_week", "period")
    )

    teacher_name = workstation.teacher.get_full_name() or workstation.teacher.username

    pdf = PDFGenerator(
        filename=f"Ratiba_{teacher_name}.pdf",
        orientation="landscape",
        language=language,
    )
    pdf.set_header(workstation.school_name)
    pdf.set_footer(teacher_name)
    pdf.add_title(f"{labels['title']} - {teacher_name.upper()}")

    location_bits = [workstation.district]
    if workstation.region:
        location_bits.append(workstation.region)
    pdf.add_paragraph(" - ".join(location_bits), small=True)

    if not rows:
        pdf.add_paragraph(labels["no_entries"])
        return pdf.build()

    periods = sorted({r.period for r in rows})
    period_times = {}
    for r in rows:
        if r.period not in period_times and r.timestart and r.timefinish:
            period_times[r.period] = f"{_time_str(r.timestart)}-{_time_str(r.timefinish)}"

    by_day = {}
    for r in rows:
        by_day.setdefault(r.day_of_week, {}).setdefault(
            r.subject_version.class_level.name if r.subject_version.class_level else "-", {}
        )[r.period] = r

    for day in sorted(by_day.keys()):
        pdf.add_subsection(day_labels.get(day, str(day)))

        header = [labels["class_col"]] + [str(p) for p in periods]
        time_row = [labels["time_row"]] + [period_times.get(p, "") for p in periods]
        table_data = [header, time_row]

        for class_name in sorted(by_day[day].keys()):
            period_map = by_day[day][class_name]
            row = [class_name]
            for p in periods:
                entry = period_map.get(p)
                row.append(entry.subject_version.subject.name if entry else "")
            table_data.append(row)

        pdf.add_table(table_data)

    return pdf.build()
