# syllabus/serializers/question_serializers.py

from rest_framework import serializers

from syllabus.models.question import Passage, Question


class PassageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passage
        fields = ["id", "learning_activity", "title", "text", "is_listening", "language"]
        read_only_fields = ("id",)


class QuestionSerializer(serializers.ModelSerializer):
    learning_activity_name = serializers.CharField(source="learning_activity.name", read_only=True)
    passage_text = serializers.CharField(source="passage.text", read_only=True, default="")

    class Meta:
        model = Question
        fields = [
            "id", "learning_activity", "learning_activity_name", "question_type", "difficulty",
            "prompt", "options", "word_bank", "correct_answer", "solution_steps",
            "passage", "passage_text", "diagram_image", "marks", "source", "language",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, data):
        instance = self.instance
        question_type = data.get("question_type", getattr(instance, "question_type", None))
        solution_steps = data.get("solution_steps", getattr(instance, "solution_steps", ""))
        passage = data.get("passage", getattr(instance, "passage", None))
        diagram_image = data.get("diagram_image", getattr(instance, "diagram_image", None))

        errors = {}
        if question_type == Question.QuestionType.CALCULATION and not solution_steps:
            errors["solution_steps"] = "Calculation questions must include worked solution steps."
        if question_type == Question.QuestionType.COMPREHENSION and not passage:
            errors["passage"] = "Comprehension questions must reference a passage."
        if question_type == Question.QuestionType.MAP_DIAGRAM and not diagram_image:
            errors["diagram_image"] = "Map/diagram questions must include an image."
        if errors:
            raise serializers.ValidationError(errors)
        return data
