# syllabus/admins/__init__.py
"""
Auto-import all admin modules for the syllabus app.
This ensures Django registers all admin classes automatically.
"""

from .class_level_admin import *
from .learning_activity_admin import *
from .specific_competence_admin import *
from .specific_learning_activity_admin import *
from .subject_admin import *
from .subject_version_admin import *
from .syllabus_version_admin import *
from .teacher_workstation_admin import *
from .timetable_admin import *
from .annual_calendar_admin import *
from .lesson_sentence_admin import *
from .main_competence_admin import *
