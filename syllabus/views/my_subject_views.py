# syllabus/views/my_subject_views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from syllabus.models.teacher_workstation import TeacherWorkStation
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.timetable import TimeTable

from syllabus.serializers.my_subject_serializer import MySubjectSerializer

class MySubjectsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        teacher = request.user

        # Pata workstation ya mwalimu
        workstation = TeacherWorkStation.objects.filter(teacher=teacher).first()
        if not workstation:
            # Hakuna workstation, frontend itaonesha modal
            return Response([])

        # Pata timetable za mwalimu huyu
        timetables = TimeTable.objects.filter(workstation=workstation)

        if timetables.exists():
            # Chukua query parameter q (kwa search)
            q = request.GET.get("q", "").strip()

            # Filter subject_versions zilizopo kwenye timetable
            subject_versions = SubjectVersion.objects.filter(
                id__in=timetables.values_list("subject_version_id", flat=True)
            ).select_related("subject", "class_level", "syllabus_version")

            if q:
                subject_versions = subject_versions.filter(
                    subject__name__icontains=q
                )

        else:
            subject_versions = []

        serializer = MySubjectSerializer(subject_versions, many=True)
        return Response(serializer.data)