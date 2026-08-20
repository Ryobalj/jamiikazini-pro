# syllabus/services/master_timetable_pdf_builder.py
from syllabus.services.pdf_base import PDFGenerator
from syllabus.services.timetable_pdf_builder import DAY_LABELS, _time_str
from syllabus.models.master_timetable import ActivityType, TimetableSlot

LABELS = {
    "sw": {
        "title": "RATIBA KUU YA MASOMO",
        "class_col": "DARASA",
        "time_row": "MUDA",
        "whole_school": "SHULE NZIMA",
        "no_entries": "Bado hakuna ratiba iliyotengenezwa - bofya 'Tengeneza' kwanza.",
        "routine_heading": "Utaratibu wa Kila Siku",
    },
    "en": {
        "title": "SCHOOL MASTER TIMETABLE",
        "class_col": "CLASS",
        "time_row": "TIME",
        "whole_school": "WHOLE SCHOOL",
        "no_entries": "No timetable has been generated yet - click 'Generate' first.",
        "routine_heading": "Daily Routine",
    },
}


def _cell_text(slot, language: str) -> str:
    if slot.assignment_id:
        subject = slot.assignment.subject_version.subject.name
        initials = slot.assignment.teacher.initials
        return f"{subject} ({initials})"
    if slot.activity_type_id:
        return slot.activity_type.label_sw if language == "sw" else slot.activity_type.label_en
    return slot.custom_label or ""


def _build_grid_bytes(roster, language: str, teacher_id=None, class_level_id=None):
    labels = LABELS.get(language, LABELS["sw"])
    day_labels = DAY_LABELS.get(language, DAY_LABELS["sw"])

    period_slots = list(roster.period_slots.order_by("order"))

    slots_qs = roster.slots.select_related(
        "period_slot", "class_level", "activity_type",
        "assignment", "assignment__teacher", "assignment__subject_version__subject",
    )
    if teacher_id:
        slots_qs = slots_qs.filter(assignment__teacher_id=teacher_id)
    if class_level_id:
        slots_qs = slots_qs.filter(class_level_id=class_level_id)
    slots = list(slots_qs)

    school_name = roster.owner.school_name
    pdf = PDFGenerator(
        filename=f"{roster.name.replace(' ', '_')}.pdf",
        orientation="landscape",
        language=language,
    )
    pdf.set_header(school_name)
    pdf.add_title(f"{labels['title']} - {roster.name.upper()}")

    routine_types = ActivityType.objects.filter(is_fixed_routine=True).order_by("default_order")
    if routine_types.exists():
        routine_text = ", ".join(
            (rt.label_sw if language == "sw" else rt.label_en) for rt in routine_types
        )
        pdf.add_paragraph(f"{labels['routine_heading']}: {routine_text}", small=True)

    if not period_slots or not slots:
        pdf.add_paragraph(labels["no_entries"])
        return pdf.build()

    class_names = sorted({
        s.class_level.name for s in slots if s.class_level_id
    })

    by_day = {}
    whole_school_by_day = {}
    for s in slots:
        if s.class_level_id is None:
            whole_school_by_day.setdefault(s.day_of_week, {})[str(s.period_slot_id)] = s
        else:
            by_day.setdefault(s.day_of_week, {}).setdefault(s.class_level.name, {})[str(s.period_slot_id)] = s

    all_days = sorted(set(by_day.keys()) | set(whole_school_by_day.keys()))
    for day in all_days:
        pdf.add_subsection(day_labels.get(day, str(day)))

        header = [labels["class_col"]] + [ps.label for ps in period_slots]
        time_row = [labels["time_row"]] + [
            f"{_time_str(ps.timestart)}-{_time_str(ps.timefinish)}" if ps.timestart and ps.timefinish else ""
            for ps in period_slots
        ]
        table_data = [header, time_row]

        day_whole_school = whole_school_by_day.get(day, {})
        rows_for_day = class_names if not class_level_id else [
            n for n in class_names if by_day.get(day, {}).get(n)
        ]
        for class_name in rows_for_day:
            period_map = by_day.get(day, {}).get(class_name, {})
            row = [class_name]
            for ps in period_slots:
                key = str(ps.id)
                if ps.is_break:
                    row.append("")
                    continue
                whole_school_slot = day_whole_school.get(key)
                if whole_school_slot:
                    row.append(_cell_text(whole_school_slot, language))
                    continue
                entry = period_map.get(key)
                row.append(_cell_text(entry, language) if entry else "")
            table_data.append(row)

        pdf.add_table(table_data)

    return pdf.build()


def build_master_timetable_pdf(roster, language: str = "sw", teacher_id=None, class_level_id=None) -> bytes:
    return _build_grid_bytes(roster, language, teacher_id=teacher_id, class_level_id=class_level_id)
