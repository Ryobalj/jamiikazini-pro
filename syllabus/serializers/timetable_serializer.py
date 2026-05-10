# syllabus/serializers/timetable_serializer.py
from rest_framework import serializers
from syllabus.models.timetable import TimeTable

class TimeTableSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject_version.subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject_version.subject.code", read_only=True)
    class_level_name = serializers.CharField(source="subject_version.class_level.name", read_only=True)
    syllabus_year = serializers.IntegerField(source="subject_version.syllabus_version.year", read_only=True)
    is_english = serializers.BooleanField(source="subject_version.is_english", read_only=True)
    is_awali = serializers.BooleanField(source="subject_version.is_awali", read_only=True)
    periods_per_week = serializers.IntegerField(source="subject_version.subject.periods_per_week", read_only=True)
    
    # Optional display fields - za kuonyesha tu
    workstation_display = serializers.SerializerMethodField()
    subject_display = serializers.SerializerMethodField()
    class_level_display = serializers.SerializerMethodField()

    class Meta:
        model = TimeTable
        fields = [
            "id",
            "workstation",
            "subject_version",
            "subject_name",
            "subject_code",
            "class_level_name",
            "syllabus_year",
            "is_english",
            "is_awali",
            "periods_per_week",
            "period",
            "timestart",
            "timefinish",
            "registeredboys",
            "registeredgirls",
            "status",
            "created_at",
            "updated_at",
            "workstation_display",
            "subject_display",
            "class_level_display",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    # -----------------------------
    # Display fields (optional)
    # -----------------------------
    def get_workstation_display(self, obj):
        if not obj.workstation:
            return "No workstation"
        ws = obj.workstation
        teacher_name = ws.teacher.get_full_name() if ws.teacher else ws.teacher.username
        return f"{teacher_name} — {ws.school_name}"

    def get_subject_display(self, obj):
        if not obj.subject_version or not obj.subject_version.subject:
            return "No subject"
        sv = obj.subject_version
        return f"{sv.subject.name} ({sv.syllabus_version.year})"

    def get_class_level_display(self, obj):
        if not obj.subject_version or not obj.subject_version.class_level:
            return "No class level"
        return obj.subject_version.class_level.name

    # -----------------------------
    # SIMPLIFIED VALIDATION
    # -----------------------------
    def validate(self, data):
        """
        Validation simplified - only check required fields
        """
        # Subject version ni required
        if 'subject_version' not in data and not self.instance:
            raise serializers.ValidationError({
                "subject_version": "Subject version is required."
            })

        # Workstation ni required
        if 'workstation' not in data and not self.instance:
            raise serializers.ValidationError({
                "workstation": "Workstation is required."
            })

        # Period, timestart, timefinish sio required - validation imeondolewa
        
        return data

    # -----------------------------
    # CREATE METHOD (optional - kuweka defaults)
    # -----------------------------
    def create(self, validated_data):
        """
        Create timetable with optional fields
        """
        # Hakuna logic maalum inahitajika - fields zote ziko optional
        return TimeTable.objects.create(**validated_data)