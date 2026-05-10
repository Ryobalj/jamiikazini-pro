# syllabus/serializers/my_subject_serializer.py

from rest_framework import serializers
from syllabus.models import SubjectVersion

class MySubjectSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="subject.name")
    code = serializers.CharField(source="subject.code")
    description = serializers.CharField(source="subject.description")
    periods_per_week = serializers.IntegerField(source="subject.periods_per_week")
    class_level = serializers.CharField(source="class_level.name")
    syllabus_year = serializers.IntegerField(source="syllabus_version.year")

    class Meta:
        model = SubjectVersion
        fields = [
            "id",
            "name",
            "code",
            "description",
            "periods_per_week",
            "class_level",
            "syllabus_year",
            "is_english",
            "is_awali",
        ]