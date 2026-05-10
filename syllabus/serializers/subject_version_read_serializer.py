# syllabus/serializers/subject_version_read_serializer.py
from rest_framework import serializers
from syllabus.models import SubjectVersion

class SubjectVersionReadSerializer(serializers.ModelSerializer):
    subject = serializers.CharField(source="subject.name", read_only=True)
    class_level = serializers.CharField(source="class_level.name", read_only=True)
    syllabus_year = serializers.IntegerField(
        source="syllabus_version.year",
        read_only=True
    )

    class Meta:
        model = SubjectVersion
        fields = [
            "id",
            "subject",
            "class_level",
            "syllabus_year",
        ]