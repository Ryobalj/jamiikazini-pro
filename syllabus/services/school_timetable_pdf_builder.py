# syllabus/services/school_timetable_pdf_builder.py

from syllabus.services.pdf_base import PDFGenerator
from syllabus.services.timetable_pdf_builder import DAY_LABELS, _time_str
from syllabus.models.timetable import TimeTable

LABELS = {
    "sw": {
        "title": "RATIBA KUU YA MASOMO",
        "class_col": "DARASA",
        "time_row": "MUDA",
        "no_entries": "Hakuna vipindi vilivyowekwa bado shuleni hapa.",
    },
    "en": {
        "title": "SCHOOL MASTER TIMETABLE",
        "class_col": "CLASS",
        "time_row": "TIME",
        "no_entries": "No periods have been set up at this school yet.",
    },
}


def _teacher_initials(teacher):
    name = (teacher.get_full_name() or teacher.username or "").strip()
    parts = [p for p in name.split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "??"


def build_school_timetable_pdf(school_name: str, language: str = "sw") -> bytes:
    """Whole-school master timetable, aggregated across every teacher's
    workstation at this school - mirrors the real 'Ratiba Kuu ya Shule'
    layout (day -> one row per class -> period columns, cell shows
    'Subject (Teacher Initials)')."""
    labels = LABELS.get(language, LABELS["sw"])
    day_labels = DAY_LABELS.get(language, DAY_LABELS["sw"])

    rows = list(
        TimeTable.objects.filter(
            workstation__school_name=school_name,
            workstation__is_active=True,
            day_of_week__isnull=False,
            period__isnull=False,
        )
        .select_related(
            "workstation__teacher",
            "subject_version__subject",
            "subject_version__class_level",
        )
        .order_by("day_of_week", "period")
    )

    pdf = PDFGenerator(
        filename=f"Ratiba_Kuu_{school_name}.pdf",
        orientation="landscape",
        language=language,
    )
    pdf.set_header(school_name)
    pdf.add_title(f"{labels['title']} - {school_name.upper()}")

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
        class_name = r.subject_version.class_level.name if r.subject_version.class_level else "-"
        by_day.setdefault(r.day_of_week, {}).setdefault(class_name, {})[r.period] = r

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
                if entry:
                    subject = entry.subject_version.subject.name
                    initials = _teacher_initials(entry.workstation.teacher)
                    row.append(f"{subject} ({initials})")
                else:
                    row.append("")
            table_data.append(row)

        pdf.add_table(table_data)

    return pdf.build()
