# kiini/serializers/department_serializers.py

from rest_framework import serializers
from kiini.models.department import Department

class DepartmentSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    created = serializers.DateTimeField(source='created_at', read_only=True)
    modified = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Department
        fields = [
            'id',
            'institution',
            'institution_name',
            'name',
            'description',
            'is_active',
            'created',
            'modified',
        ]
        # institution huwekwa na view kutoka nested URL (perform_create) -
        # bila kuifanya read-only, POST ingedai institution mwilini (400)
        read_only_fields = ['id', 'institution', 'created', 'modified']