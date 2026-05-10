# syllabus/urls/nested_routers.py

from rest_framework_nested.routers import NestedDefaultRouter
from .router import router

from syllabus.views.specific_competence_views import SpecificCompetenceViewSet
from syllabus.views.learning_activity_views import LearningActivityViewSet
from syllabus.views.specific_learning_activity_views import SpecificLearningActivityViewSet

# -----------------------------------------------------
# LEVEL 1: main-competence → specific-competences
# -----------------------------------------------------
main_comp_nested = NestedDefaultRouter(router, r"main-competences", lookup="main_competence")
main_comp_nested.register(
    r"specific-competences",
    SpecificCompetenceViewSet,
    basename="main-specific-competence"
)

# -----------------------------------------------------
# LEVEL 2: specific-competence → learning-activities
# -----------------------------------------------------
specific_nested = NestedDefaultRouter(router, r"specific-competences", lookup="specific_competence")
specific_nested.register(
    r"learning-activities",
    LearningActivityViewSet,
    basename="specific-learning-activity"
)

# -----------------------------------------------------
# LEVEL 3: learning-activity → specific-learning-activities
# -----------------------------------------------------
activity_nested = NestedDefaultRouter(router, r"learning-activities", lookup="learning_activity")
activity_nested.register(
    r"specific-learning-activities",
    SpecificLearningActivityViewSet,
    basename="learning-activity-specific"
)

urlpatterns = (
    main_comp_nested.urls +
    specific_nested.urls +
    activity_nested.urls
)