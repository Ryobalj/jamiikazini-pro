# syllabus/tests/test_admin/test_learning_activity_admin.py

import pytest
from django.contrib.admin.sites import site
from syllabus.models.learning_activity import LearningActivity
from syllabus.admins.learning_activity_admin import LearningActivityAdmin, LearningActivityInline
from syllabus.models.specific_competence import SpecificCompetence

@pytest.mark.django_db
class TestLearningActivityAdmin:

    def test_admin_registration(self):
        # Kagua kama model ime-register kwenye admin site
        model_admin = site._registry.get(LearningActivity)
        assert isinstance(model_admin, LearningActivityAdmin)

    def test_list_display_and_filter(self):
        admin_instance = LearningActivityAdmin(LearningActivity, site)
        expected_list_display = ("name", "specific_competence", "order", "created_at", "updated_at")
        assert admin_instance.list_display == expected_list_display
        assert admin_instance.list_filter == ("specific_competence",)
        assert admin_instance.search_fields == ("name", "specific_competence__name")
        assert admin_instance.readonly_fields == ("order", "created_at", "updated_at")
        assert admin_instance.ordering == ("specific_competence", "order")
        assert admin_instance.autocomplete_fields == ("specific_competence",)

    def test_inline_admin_settings(self):
        inline = LearningActivityInline(SpecificCompetence, site)
        assert inline.model == LearningActivity
        assert inline.extra == 0
        assert inline.readonly_fields == ("order",)
        assert inline.ordering == ("order",)
        assert inline.show_change_link is True
        assert inline.fields == ("name", "order")