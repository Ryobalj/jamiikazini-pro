from rest_framework import serializers
from syllabus.models.subject import Subject


class SubjectLookupSerializer(serializers.ModelSerializer):
    value = serializers.UUIDField(source="id")
    label = serializers.CharField(source="name")

    class Meta:
        model = Subject
        fields = [
            "value",
            "label",
            "code",
        ]