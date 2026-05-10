# search/documents/branch_document.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from businesses.models.branch import Branch

@registry.register_document
class BranchDocument(Document):
    business = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
    })

    services = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
    })

    location = fields.GeoPointField()

    class Index:
        name = 'branches'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Branch
        fields = [
            'id',
            'name',
            'description',
            'phone',
            'email',
            'is_active',
            'created_at',
        ]