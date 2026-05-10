# jamiikazini/syllabus/serializers/lesson_sentence_serializer.py

from rest_framework import serializers
from syllabus.models.lesson_sentence import LessonSentence


class LessonSentenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonSentence
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def _val(self, data, field):
        return data.get(field) if field in data else getattr(self.instance, field, None)

    # Validation
    def validate_category(self, value):
        if not value:
            raise serializers.ValidationError("Category lazima ichaguliwe.")
        valid_categories = dict(LessonSentence.Category.choices)
        if value not in valid_categories:
            raise serializers.ValidationError("Category si sahihi.")
        return value

    def validate_is_active(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError("is_active lazima iwe boolean.")
        return value

    def validate_is_awali(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError("is_awali lazima iwe boolean.")
        return value

    def validate_language(self, value):
        if value not in ["sw", "en"]:
            raise serializers.ValidationError("language lazima iwe 'sw' au 'en'.")
        return value

    # Global validation and cleaning
    def validate(self, data):
        data = super().validate(data)

        teaching_sw = (self._val(data, "teaching_sw") or "").strip()
        teaching_en = (self._val(data, "teaching_en") or "").strip()

        if not teaching_sw and not teaching_en:
            raise serializers.ValidationError({
                "teaching_sw": "Weka 'teaching_sw' au 'teaching_en' (angalau moja)."
            })

        TEXT_FIELDS = [
            "teaching_sw", "learning_sw", "indicator_primary_sw", "indicator_secondary_sw",
            "teaching_en", "learning_en", "indicator_primary_en", "indicator_secondary_en",
            "reflection_sw", "reflection_comment_sw",
            "reflection_en", "reflection_comment_en",
        ]

        for field in TEXT_FIELDS:
            value = self._val(data, field)
            data[field] = value.strip() if value else None

        return data