# syllabus/i18n/en.py

# -----------------------------
# SCHOOL-TYPE PREFIX (derived from the muhtasari's curriculum family, not
# typed by the teacher — see SubjectVersion.is_awali/is_sekondari)
# -----------------------------
SCHOOL_TYPE_PREFIX = {
    "awali": "Pre-Primary School",
    "msingi": "Primary School",
    "sekondari": "Secondary School",
}

# -----------------------------
# LESSON PLAN LABELS
# -----------------------------
LESSON_PLAN = {
    "title": "LESSON PLAN",

    # SECTION I: IDENTIFICATION
    "school_name": "School Name",
    "teacher_name": "Teacher Name",
    "main_competence": "Main Competence",
    "class_level": "Class",
    "date": "Date",
    "period": "Period",
    "duration": "Duration",

    # SECTION II: STUDENT COUNT
    "students_section": "STUDENT COUNT",
    "registered": "Registered",
    "attended": "Attended",
    "boys": "Boys",
    "girls": "Girls",
    "total": "Total",

    # SECTION III: LESSON INFORMATION
    "lesson_info": "LESSON INFORMATION",
    "specific_competence": "Specific Competence",
    "main_activity": "Main Activity",
    "specific_activity": "Specific Activity",
    "teaching_aids": "Teaching Aids",
    "reference": "Reference",

    # SECTION IV: LESSON STEPS
    "steps_section": "LESSON STEPS",
    "steps": [
        "Introduction",
        "Development",
        "Reinforcement",
        "Conclusion",
    ],
    "step": "Teaching Step",  # header of first column
    "time": "Time",
    "teaching_activity": "Teaching Activity",
    "learning_activity": "Learning Activity",
    "assessment": "Assessment Indicator",

    # SECTION V: LESSON NOTES & EXERCISE
    "lesson_notes": "LESSON NOTES",
    "notes_intro": "Introduction",
    "notes_details": "Further Details",
    "notes_illustrations": "Worked Examples",
    "notes_examples": "Everyday Life Applications",
    "exercise": "EXERCISE",
    "answer": "Answer",
    "minutes": "Minutes",

    # SECTION VI: REFLECTION
    "reflection": "REFLECTION",
    "teaching_comment": "Reflection",
    "assessment_comment": "Teaching Assessment",
    "next_plan": "Remarks",
}

# -----------------------------
# SCHEME OF WORK LABELS
# -----------------------------
SCHEME_LABELS = {
    "document_title": "SCHEME OF WORK",
    "council": "DISTRICT COUNCIL",
    "school_name": "PRIMARY SCHOOL",
    "teacher_name": "TEACHER NAME",
    "class_level": "CLASS",
    "term": "TERM",
    "subject": "SUBJECT",
    "year": "YEAR",

    "objectives": "OBJECTIVES",
    "objectives_list": [],
    "objectives_empty": "No specific objectives have been defined.",

    # Fill-in labels for the header identification table — Title Case +
    # colon (not forced uppercase), matching the convention used for
    # every other fill-in label in these documents.
    "field_council": "Council",
    "field_school": "School",
    "field_teacher": "Teacher",
    "field_class": "Class",
    "field_subject": "Subject",
    "field_year": "Year",
    "field_term": "Term",

    "headers": [
        "MAIN COMPETENCE",
        "SPECIFIC COMPETENCE",
        "TEACHING ACTIVITIES",
        "LEARNING ACTIVITIES",
        "MONTH",
        "WEEK",
        "PERIODS",
        "METHODS",
        "REFERENCES",
        "TEACHING AIDS",
        "ASSESSMENT",
        "REMARKS",
    ],
}

# -----------------------------
# CALENDAR / SCHEDULE VOCAB (used by SchemeTimelineBuilder)
# -----------------------------
MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

# Content for weeks left over after real syllabus topics are exhausted,
# for national-exam class levels (see SchemeTimelineBuilder).
MARUDIO_CONTENT = {
    "main_competence": "REVISION",
    "specific_competence": "Revision of challenging topics",
    "learning_activity": "Reviewing topics students found challenging",
    "student_activity": "Doing tests and revision exercises on challenging topics",
    "methodology": "Tests, practice exams and discussion",
    "assessment_criteria": "Participation and accuracy",
    "teaching_aids": "Test papers, practice cards",
    "references": "Reference materials",
}
EXAM_PREP_CONTENT = {
    "main_competence": "NATIONAL EXAM PREPARATION",
    "specific_competence": "Preparing for the national exam",
    "learning_activity": "Practising past exam papers",
    "student_activity": "Practising past exam papers",
    "methodology": "Exam practice",
    "assessment_criteria": "Participation and accuracy",
    "teaching_aids": "Past papers",
    "references": "Reference materials",
}

# Fallback defaults used only when an activity's own data omits a field.
ACTIVITY_FIELD_DEFAULTS = {
    "method": "Discussion and exercises",
    "assessment_criteria": "Participation and exercises",
    "teaching_aids": "Cards, charts, textbook",
    "references": "Student's textbook",
}