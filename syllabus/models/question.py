# syllabus/models/question.py

from django.core.exceptions import ValidationError
from django.db import models
from kiini.models.base import UUIDModel, TimeStampedModel


class Passage(UUIDModel, TimeStampedModel):
    """A shared reading/listening passage that one or more comprehension
    questions are based on (see Question.passage)."""

    learning_activity = models.ForeignKey(
        "syllabus.LearningActivity",
        on_delete=models.CASCADE,
        related_name="passages",
    )
    title = models.CharField(max_length=255, blank=True, default="")
    text = models.TextField(help_text="The passage text itself.")
    is_listening = models.BooleanField(
        default=False,
        help_text=(
            "True if this passage is meant to be read aloud by the "
            "invigilator (listening comprehension) rather than printed "
            "for the pupil to read."
        ),
    )
    language = models.CharField(
        max_length=2, choices=[("sw", "Swahili"), ("en", "English")], default="sw"
    )

    class Meta:
        verbose_name = "Passage"
        verbose_name_plural = "Passages"

    def __str__(self):
        return self.title or self.text[:50]


class Question(UUIDModel, TimeStampedModel):
    """One item in the question bank, grounded in the pupils' book and
    tagged to a topic (LearningActivity) so it can be pulled into a
    generated paper by subject/class/topic/type/difficulty."""

    class QuestionType(models.TextChoices):
        MCQ = "mcq", "Multiple Choice"
        MATCHING = "matching", "Matching"
        FILL_BLANK = "fill_blank", "Fill in the Blank"
        SHORT_ANSWER = "short_answer", "Short Answer"
        CALCULATION = "calculation", "Calculation"
        SEQUENCING = "sequencing", "Sequencing"
        MAP_DIAGRAM = "map_diagram", "Map/Diagram"
        COMPREHENSION = "comprehension", "Comprehension"
        TRUE_FALSE = "true_false", "True/False"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    learning_activity = models.ForeignKey(
        "syllabus.LearningActivity",
        on_delete=models.CASCADE,
        related_name="questions",
        help_text="Topic this question belongs to.",
    )
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    difficulty = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )
    prompt = models.TextField(help_text="The question text itself.")
    options = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "For mcq: list of choice strings. For matching: list of "
            "{'left': str, 'right': str} pairs."
        ),
    )
    word_bank = models.JSONField(
        default=list,
        blank=True,
        help_text="For fill_blank questions offered from a word bank: list of candidate words/phrases.",
    )
    correct_answer = models.TextField(
        help_text="The correct answer/answer key. Required on every question."
    )
    solution_steps = models.TextField(
        blank=True,
        default="",
        help_text="Full worked solution steps. Required for calculation-type questions.",
    )
    passage = models.ForeignKey(
        Passage,
        on_delete=models.CASCADE,
        related_name="questions",
        null=True,
        blank=True,
        help_text="Shared passage this question is based on (comprehension type).",
    )
    diagram_image = models.ImageField(
        upload_to="quiz_diagrams/",
        null=True,
        blank=True,
        help_text="Map/diagram image this question refers to (map_diagram type).",
    )
    marks = models.PositiveIntegerField(
        default=1,
        help_text="Default marks this question is worth when a format doesn't override it.",
    )
    source = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text=(
            "Book/page citation this question is grounded in, e.g. "
            "'TET(2023), HISABATI, KITABU CHA MWANAFUNZI, DARASA LA TATU'."
        ),
    )
    language = models.CharField(
        max_length=2, choices=[("sw", "Swahili"), ("en", "English")], default="sw"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["learning_activity", "difficulty", "created_at"]

    def clean(self):
        errors = {}
        if self.question_type == self.QuestionType.CALCULATION and not self.solution_steps:
            errors["solution_steps"] = "Calculation questions must include worked solution steps."
        if self.question_type == self.QuestionType.COMPREHENSION and not self.passage_id:
            errors["passage"] = "Comprehension questions must reference a passage."
        if self.question_type == self.QuestionType.MAP_DIAGRAM and not self.diagram_image:
            errors["diagram_image"] = "Map/diagram questions must include an image."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"[{self.get_question_type_display()}/{self.difficulty}] {self.prompt[:50]}"
