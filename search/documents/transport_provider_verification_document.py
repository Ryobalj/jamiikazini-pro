# search/documents/transport_provider_verification_document.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from logistics.models.transport_provider_verification import TransportProviderVerification
from accounts.models import User
from kiini.models.institution import Institution
from gov_integration.models.verification_request import VerificationRequest


@registry.register_document
class TransportProviderVerificationDocument(Document):
    user = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'username': fields.TextField(),
        'email': fields.TextField(),
    })

    institution = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    nida_verification = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'status': fields.TextField(),
        'verified_at': fields.DateField(),
    })

    driving_license_verification = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'status': fields.TextField(),
        'verified_at': fields.DateField(),
    })

    vehicle_license_verification = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'status': fields.TextField(),
        'verified_at': fields.DateField(),
    })

    latra_permit_verification = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'status': fields.TextField(),
        'verified_at': fields.DateField(),
    })

    class Index:
        name = 'transport_provider_verifications'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = TransportProviderVerification
        fields = [
            'overall_status',
            'notes',
            'created_at',
            'updated_at',
        ]
        related_models = [
            User,
            Institution,
            VerificationRequest,
        ]

    def get_queryset(self):
        return super().get_queryset().select_related(
            'user',
            'institution',
            'nida_verification',
            'driving_license_verification',
            'vehicle_license_verification',
            'latra_permit_verification'
        )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return [related_instance.transport_verification] if hasattr(related_instance, 'transport_verification') else []
        if isinstance(related_instance, Institution):
            return related_instance.transport_verifications.all()
        if isinstance(related_instance, VerificationRequest):
            return list(related_instance.nida_transport_verification.all()) + \
                   list(related_instance.driving_license_verification.all()) + \
                   list(related_instance.vehicle_license_verification.all()) + \
                   list(related_instance.latra_permit_verification.all())