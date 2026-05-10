# search/documents/department_document.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from kiini.models.department import Department
from kiini.models.institution import Institution

@registry.register_document
class DepartmentDocument(Document):
    institution = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    class Index:
        name = 'departments'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Department
        fields = [
            'id',
            'name',
            'created_at',
            'updated_at',
            # 'institution_id',  # Ondoa hii, inaleta error
        ]
        related_models = [Institution]

    def get_queryset(self):
        return super().get_queryset().select_related('institution')

    def prepare_institution(self, instance):
        institution = instance.institution
        if not institution:
            return None
        return {
            'id': institution.id,
            'name': institution.name,
        }

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Institution):
            return related_instance.departments.all()