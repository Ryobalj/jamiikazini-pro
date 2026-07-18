# search/documents/transport_provider_verification_document.py

from django.conf import settings
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

    # Institution is UUID-keyed - KeywordField, not IntegerField.
    institution = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(),
    })
    institution_id = fields.KeywordField(attr='institution.id')

    # NOTE: VerificationRequest has no verified_at field (verified against
    # gov_integration/models/verification_request.py) - updated_at (bumped by
    # auto_now=True whenever .verify() saves) is used instead as the closest
    # real "last touched" timestamp, rather than a field that would always be null.
    nida_verification = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'status': fields.TextField(),
        'updated_at': fields.DateField(),
    })

    driving_license_verification = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'status': fields.TextField(),
        'updated_at': fields.DateField(),
    })

    vehicle_license_verification = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'status': fields.TextField(),
        'updated_at': fields.DateField(),
    })

    latra_permit_verification = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'status': fields.TextField(),
        'updated_at': fields.DateField(),
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
            'id',
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

    def prepare_institution(self, instance):
        institution = instance.institution
        if not institution:
            return None
        return {'id': str(institution.id), 'name': institution.name}

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return [related_instance.transport_verification] if hasattr(related_instance, 'transport_verification') else []
        if isinstance(related_instance, Institution):
            return related_instance.transport_verifications.all()
        if isinstance(related_instance, VerificationRequest):
            # Each of these is a reverse OneToOne accessor (a single object or
            # RelatedObjectDoesNotExist), not a manager - .all() would crash here.
            results = []
            for attr in (
                'nida_transport_verification',
                'driving_license_verification',
                'vehicle_license_verification',
                'latra_permit_verification',
            ):
                obj = getattr(related_instance, attr, None)
                if obj:
                    results.append(obj)
            return results

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                TransportProviderVerification.objects.select_related(
                    "user", "institution",
                    "nida_verification", "driving_license_verification",
                    "vehicle_license_verification", "latra_permit_verification",
                ),
                search_fields=("notes", "overall_status"),
            )
        return super().search(using=using, index=index, **kwargs)
