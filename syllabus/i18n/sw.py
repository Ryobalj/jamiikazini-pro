# syllabus/i18n/sw.py

# -----------------------------
# SCHOOL-TYPE PREFIX (derived from the muhtasari's curriculum family, not
# typed by the teacher — see SubjectVersion.is_awali/is_sekondari)
# -----------------------------
SCHOOL_TYPE_PREFIX = {
    "awali": "Shule ya Awali",
    "msingi": "Shule ya Msingi",
    "sekondari": "Shule ya Sekondari",
}

# -----------------------------
# LESSON PLAN LABELS
# -----------------------------
LESSON_PLAN = {
    "title": "ANDALIO LA SOMO",
    "school_name": "Jina la Shule",
    "teacher_name": "Jina la Mwalimu",
    "main_competence": "Umahiri Mkuu",
    "class_level": "Darasa la",
    "date": "Tarehe",
    "period": "Kipindi cha",
    "duration": "Muda",
    "students_section": "IDADI YA WANAFUNZI",
    "registered": "Walioandikishwa",
    "attended": "Waliohudhuria",
    "boys": "Wavulana",
    "girls": "Wasichana",
    "total": "Jumla",
    "lesson_info": "TAARIFA ZA SOMO",
    "specific_competence": "Umahiri Mahsusi",
    "main_activity": "Shughuli Kuu",
    "specific_activity": "Shughuli Mahsusi",
    "teaching_aids": "Zana za Kufundishia",
    "reference": "Rejea",
    "steps_section": "HATUA ZA SOMO",
    "steps": [
        "Utangulizi",
        "Kuendeleza ujenzi wa umahiri",
        "Kubuni",
        "Tathimini",
    ],
    "step": "Hatua za Ufundishaji",
    "time": "Muda",
    "teaching_activity": "Shughuli za Ufundishaji",
    "learning_activity": "Shughuli za Ujifunzaji",
    "assessment": "Vigezo vya Upimaji",
    "lesson_notes": "NUKUU ZA SOMO",
    "notes_intro": "Utangulizi",
    "notes_details": "Maelezo Zaidi",
    "notes_illustrations": "Mifano",
    "notes_examples": "Matumizi Katika Maisha ya Kila Siku",
    "exercise": "ZOEZI",
    "answer": "Jibu",
    "minutes": "Dakika",
    "reflection": "MAONI NA TAFAKURI",
    "teaching_comment": "Tafakuri",
    "assessment_comment": "Tathmini ya Ufundishaji",
    "next_plan": "Maoni",
}

SCHEME_LABELS = {
    "document_title": "AZIMIO LA KAZI",
    "council": "HALIMA SHAURI YA WILAYA",
    "school_name": "SHULE YA MSINGI",
    "teacher_name": "JINA LA MWALIMU",
    "class_level": "DARASA LA",
    "term": "MUHULA",
    "subject": "SOMO",
    "year": "MWAKA",

    "objectives": "MALENGO",
    "objectives_list": [],
    "objectives_empty": "Hakuna malengo maalum yaliyobainishwa.",

    # Fill-in labels for the header identification table — Title Case +
    # colon (not forced uppercase), matching the convention used for
    # every other fill-in label in these documents.
    "field_council": "Halmashauri",
    "field_school": "Shule",
    "field_teacher": "Mwalimu",
    "field_class": "Darasa",
    "field_subject": "Somo",
    "field_year": "Mwaka",
    "field_term": "Muhula",

    "headers": [
        "UMAHIRI MKUU",
        "UMAHIRI MAHUSUSI",
        "SHUGHULI ZA UFUNDISHAJI",
        "SHUGHULI ZA UJIFUNZAJI",
        "MWEZI",
        "WIKI",
        "VIPINDI",
        "MBINU",
        "MAREJEO",
        "ZANA",
        "UPIMAJI",
        "MAONI",
    ],
}

# -----------------------------
# CALENDAR / SCHEDULE VOCAB (used by SchemeTimelineBuilder)
# -----------------------------
MONTH_NAMES = {
    1: "Januari", 2: "Februari", 3: "Machi", 4: "Aprili",
    5: "Mei", 6: "Juni", 7: "Julai", 8: "Agosti",
    9: "Septemba", 10: "Oktoba", 11: "Novemba", 12: "Desemba",
}

# Content for weeks left over after real syllabus topics are exhausted,
# for national-exam class levels (see SchemeTimelineBuilder).
MARUDIO_CONTENT = {
    "main_competence": "MARUDIO",
    "specific_competence": "Kukagua na kufanya marudio",
    "learning_activity": "Kukagua mada zilizofunzwa",
    "student_activity": "Kufanya mazoezi ya marudio",
    "methodology": "Majadiliano na mazoezi",
    "assessment_criteria": "Ushiriki na usahihi",
    "teaching_aids": "Kadi za mazoezi",
    "references": "Vyanzo vya kumbukumbu",
}
EXAM_PREP_CONTENT = {
    "main_competence": "MAANDALIZI YA MTIHANI WA TAIFA",
    "specific_competence": "Kujiandaa na mtihani wa taifa",
    "learning_activity": "Kufanya mazoezi ya mitihani ya nyuma",
    "student_activity": "Kufanya mazoezi ya mitihani ya nyuma",
    "methodology": "Mazoezi ya mitihani",
    "assessment_criteria": "Ushiriki na usahihi",
    "teaching_aids": "Mitihani ya nyuma (past papers)",
    "references": "Vyanzo vya kumbukumbu",
}

# Fallback defaults used only when an activity's own data omits a field.
ACTIVITY_FIELD_DEFAULTS = {
    "method": "Majadiliano na mazoezi",
    "assessment_criteria": "Ushiriki na mazoezi",
    "teaching_aids": "Kadi, chati, kitabu",
    "references": "Kitabu cha mwanafunzi",
}