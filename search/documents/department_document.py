# search/documents/department_document.py

from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from kiini.models.department import Department
from kiini.models.institution import Institution

@registry.register_document
class DepartmentDocument(Document):
    # Institution is UUID-keyed - KeywordField, not IntegerField.
    institution = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
    })
    institution_id = fields.KeywordField(attr='institution.id')

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
            'description',
            'is_active',
            'created_at',
            'updated_at',
        ]
        related_models = [Institution]

    def get_queryset(self):
        return super().get_queryset().select_related('institution')

    def prepare_institution(self, instance):
        institution = instance.institution
        if not institution:
            return None
        return {
            'id': str(institution.id),
            'name': institution.name,
        }

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Institution):
            return related_instance.departments.all()

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                Department.objects.filter(is_active=True).select_related("institution"),
                search_fields=("name", "institution__name"),
            )
        return super().search(using=using, index=index, **kwargs)
