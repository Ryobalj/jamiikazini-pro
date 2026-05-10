# jamiikazini/syllabus/models/lesson_sentence.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel
import random


class LessonSentence(UUIDModel, TimeStampedModel):

    class Category(models.TextChoices):
        INTRO = "intro", _("Utangulizi / Introduction")
        DEVELOPMENT = "development", _("Kuimarisha / Development")
        CONCLUSION = "conclusion", _("Hitimisho / Conclusion")
        REFLECTION = "reflection", _("Maoni / Reflection")

    class Language(models.TextChoices):
        SW = "sw", _("Swahili")
        EN = "en", _("English")

    # ==================================================
    # CORE METADATA
    # ==================================================
    category = models.CharField(
        max_length=20,
        default = Category.INTRO,
        choices=Category.choices
    )

    language = models.CharField(
        max_length=2,
        choices=Language.choices,
        default=Language.SW
    )

    is_awali = models.BooleanField(
        default=False,
        help_text="True kwa darasa la Awali"
    )

    is_active = models.BooleanField(default=True)

    # ==================================================
    # SWAHILI CONTENT
    # ==================================================
    teaching_sw = models.TextField(blank=True, default="")
    learning_sw = models.TextField(blank=True, default="")
    indicator_primary_sw = models.TextField(blank=True, default="")
    indicator_secondary_sw = models.TextField(blank=True, default="")

    # ==================================================
    # ENGLISH CONTENT
    # ==================================================
    teaching_en = models.TextField(blank=True, default="")
    learning_en = models.TextField(blank=True, default="")
    indicator_primary_en = models.TextField(blank=True, default="")
    indicator_secondary_en = models.TextField(blank=True, default="")

    # ==================================================
    # REFLECTION
    # ==================================================
    reflection_sw = models.TextField(blank=True, default="")
    reflection_comment_sw = models.TextField(blank=True, default="")
    reflection_en = models.TextField(blank=True, default="")
    reflection_comment_en = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["category", "-created_at"]

    def __str__(self):
        return f"{self.get_category_display()} ({self.language})"

    # ==================================================
    # CONTEXT-AWARE HELPERS
    # ==================================================
    def _lang(self, ctx):
        return ctx.language

    def get_teaching(self, ctx):
        return self.teaching_sw if self._lang(ctx) == "sw" else self.teaching_en

    def get_learning(self, ctx):
        return self.learning_sw if self._lang(ctx) == "sw" else self.learning_en

    def get_indicator_primary(self, ctx):
        return (
            self.indicator_primary_sw
            if self._lang(ctx) == "sw"
            else self.indicator_primary_en
        )

    def get_indicator_secondary(self, ctx):
        return (
            self.indicator_secondary_sw
            if self._lang(ctx) == "sw"
            else self.indicator_secondary_en
        )

    def get_reflection(self, ctx):
        return self.reflection_sw if self._lang(ctx) == "sw" else self.reflection_en

    def get_reflection_comment(self, ctx):
        return (
            self.reflection_comment_sw
            if self._lang(ctx) == "sw"
            else self.reflection_comment_en
        )

    # ==================================================
    # RANDOM PICK (CONTEXT-AWARE)
    # ==================================================
    @staticmethod
    def pick_random(category, ctx):
        qs = LessonSentence.objects.filter(
            category=category,
            is_active=True,
            language=ctx.language,
            is_awali=ctx.is_awali,
        )

        if not qs.exists():
            return None

        return random.choice(list(qs))