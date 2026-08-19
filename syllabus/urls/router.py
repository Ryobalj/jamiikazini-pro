# syllabus/urls/router.py

from rest_framework.routers import DefaultRouter

# ===== VIEWS =====
from syllabus.views.main_competence_views import MainCompetenceViewSet
from syllabus.views.specific_competence_views import SpecificCompetenceViewSet
from syllabus.views.learning_activity_views import LearningActivityViewSet
from syllabus.views.specific_learning_activity_views import SpecificLearningActivityViewSet
from syllabus.views.subject_views import SubjectViewSet
from syllabus.views.subject_version_views import *
from syllabus.views.syllabus_version_views import SyllabusVersionViewSet
from syllabus.views.teacher_workstation_views import TeacherWorkStationViewSet
from syllabus.views.timetable_views import TimeTableViewSet
from syllabus.views.lesson_sentence_views import LessonSentenceViewSet
from syllabus.views.annual_calendar_views import AnnualCalendarViewSet
from syllabus.views.class_level_views import ClassLevelViewSet
from syllabus.views.exam_views import StudentViewSet, ExamViewSet
from syllabus.views.question_views import PassageViewSet, QuestionViewSet
from syllabus.views.exam_format_views import ExamFormatViewSet
from syllabus.views.generated_paper_views import GeneratedPaperViewSet


router = DefaultRouter()

# ===== ADMIN ONLY =====
router.register(r"main-competences", MainCompetenceViewSet, basename="main-competence")
router.register(r"specific-competences", SpecificCompetenceViewSet, basename="specific-competence")
router.register(r"learning-activities", LearningActivityViewSet, basename="learning-activity")
router.register(r"specific-learning-activities", SpecificLearningActivityViewSet, basename="specific-learning-activity")
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"subject-versions", SubjectVersionViewSet, basename="subjectversion")
router.register(r"syllabus-versions", SyllabusVersionViewSet, basename="syllabusversion")
router.register(r"lesson-sentences", LessonSentenceViewSet, basename="lesson-sentences")
router.register(r"annual-calendars", AnnualCalendarViewSet, basename="annualcalendar")
router.register(r"class-levels", ClassLevelViewSet, basename="classlevel")
router.register(r"passages", PassageViewSet, basename="passage")
router.register(r"questions", QuestionViewSet, basename="question")
router.register(r"exam-formats", ExamFormatViewSet, basename="examformat")


# ===== AUTHENTICATED USERS =====
router.register(r"teacher-workstations", TeacherWorkStationViewSet, basename="teacherworkstation")
router.register(r"timetables", TimeTableViewSet, basename="timetable")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"exams", ExamViewSet, basename="exam")
router.register(r"generated-papers", GeneratedPaperViewSet, basename="generatedpaper")

router.register(
    r"subject-versions-readonly",
    SubjectVersionReadOnlyViewSet,
    basename="subjectversion-readonly"
)

urlpatterns = router.urls
