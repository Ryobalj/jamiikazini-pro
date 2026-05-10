# search/documents/staff_profile_document.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from kiini.models.staff import StaffProfile
from kiini.models.institution import Institution
from kiini.models.department import Department


@registry.register_document
class StaffProfileDocument(Document):
    user = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'full_name': fields.TextField(),
        'email': fields.TextField(),
    })

    institution = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    department = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    # Field ya kusaidia filtering by institution
    institution_id = fields.IntegerField(attr='institution.id')

    class Index:
        name = 'staff_profiles'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = StaffProfile
        fields = [
            'position',
            'title',
            'phone',
            'is_active',
            'created_at',
            'updated_at',
        ]
        related_models = [
            Institution,
            Department,
            StaffProfile.user.field.related_model
        ]

    def get_queryset(self):
        return super().get_queryset().select_related(
            'user', 'institution', 'department'
        )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Institution):
            return related_instance.staff_profiles.all()
        elif isinstance(related_instance, Department):
            return related_instance.staff_profiles.all()
        elif hasattr(related_instance, 'staffprofile'):
            return [related_instance.staffprofile]
        return []