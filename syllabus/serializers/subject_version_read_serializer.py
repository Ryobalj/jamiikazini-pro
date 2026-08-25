# syllabus/serializers/subject_version_read_serializer.py
from rest_framework import serializers
from syllabus.models import SubjectVersion

class SubjectVersionReadSerializer(serializers.ModelSerializer):
    subject = serializers.CharField(source="subject.name", read_only=True)
    # The underlying Subject's own PK - needed wherever a caller has to
    # submit a bare Subject id (e.g. Exam.subjects, a Subject-keyed M2M),
    # since this serializer's own "id" is the SubjectVersion's id instead.
    subject_id = serializers.PrimaryKeyRelatedField(source="subject", read_only=True)
    class_level = serializers.CharField(source="class_level.name", read_only=True)
    class_level_id = serializers.PrimaryKeyRelatedField(source="class_level", read_only=True)
    syllabus_year = serializers.IntegerField(
        source="syllabus_version.year",
        read_only=True
    )

    class Meta:
        model = SubjectVersion
        fields = [
            "id",
            "subject",
            "subject_id",
            "class_level",
            "class_level_id",
            "syllabus_year",
        ]