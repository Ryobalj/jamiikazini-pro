# search/documents/syllabus_document.py

from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from syllabus.models.specific_learning_activity import SpecificLearningActivity


@registry.register_document
class SyllabusSearchDocument(Document):
    """
    Atomic search document for syllabus content.
    One document = one SpecificLearningActivity + full syllabus context.
    """

    # -------------------------
    # SUBJECT CONTEXT
    # -------------------------
    subject = fields.ObjectField(properties={
        "id": fields.KeywordField(),
        "name": fields.TextField(),
        "code": fields.KeywordField(),
    })

    class_level = fields.ObjectField(properties={
        "id": fields.KeywordField(),
        "name": fields.KeywordField(),
        "order": fields.IntegerField(),
    })

    syllabus_version = fields.ObjectField(properties={
        "id": fields.KeywordField(),
        "year": fields.IntegerField(),
        "is_current": fields.BooleanField(),
    })

    subject_version = fields.ObjectField(properties={
        "id": fields.KeywordField(),
        "is_english": fields.BooleanField(),
        "is_awali": fields.BooleanField(),
        "order": fields.IntegerField(),
    })

    # -------------------------
    # COMPETENCE CONTEXT
    # -------------------------
    main_competence = fields.ObjectField(properties={
        "id": fields.KeywordField(),
        "name": fields.TextField(),
        "order": fields.IntegerField(),
    })

    specific_competence = fields.ObjectField(properties={
        "id": fields.KeywordField(),
        "name": fields.TextField(),
        "order": fields.IntegerField(),
    })

    learning_activity = fields.ObjectField(properties={
        "id": fields.KeywordField(),
        "name": fields.TextField(),
        "order": fields.IntegerField(),
    })

    # -------------------------
    # SEARCHABLE CORE CONTENT
    # -------------------------
    name = fields.TextField()
    method = fields.TextField()
    leading = fields.TextField()
    assessment_criteria = fields.TextField()
    teaching_aids = fields.TextField()
    references = fields.TextField()
    periods = fields.IntegerField()
    order = fields.IntegerField()

    class Index:
        name = "syllabus_search"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    class Django:
        model = SpecificLearningActivity

    # -------------------------
    # DATA PREPARATION
    # -------------------------
    # All of the chains below walk several nullable FK hops - every step is
    # guarded so a mid-chain None (a deleted/unlinked record) degrades to a
    # None field instead of crashing the whole indexing run.

    def prepare_subject(self, instance):
        sc = instance.learning_activity and instance.learning_activity.specific_competence
        mc = sc and sc.main_competence
        sv = mc and mc.subject_version
        subject = sv and sv.subject
        if not subject:
            return None
        return {
            "id": str(subject.id),
            "name": subject.name,
            "code": subject.code,
        }

    def prepare_class_level(self, instance):
        sc = instance.learning_activity and instance.learning_activity.specific_competence
        mc = sc and sc.main_competence
        sv = mc and mc.subject_version
        cl = sv and sv.class_level
        if not cl:
            return None
        return {
            "id": str(cl.id),
            "name": cl.name,
            "order": cl.order,
        }

    def prepare_syllabus_version(self, instance):
        sc = instance.learning_activity and instance.learning_activity.specific_competence
        mc = sc and sc.main_competence
        sv = mc and mc.subject_version
        syllabus_version = sv and sv.syllabus_version
        if not syllabus_version:
            return None
        return {
            "id": str(syllabus_version.id),
            "year": syllabus_version.year,
            "is_current": syllabus_version.is_current,
        }

    def prepare_subject_version(self, instance):
        sc = instance.learning_activity and instance.learning_activity.specific_competence
        mc = sc and sc.main_competence
        sv = mc and mc.subject_version
        if not sv:
            return None
        return {
            "id": str(sv.id),
            "is_english": sv.is_english,
            "is_awali": sv.is_awali,
            "order": sv.order,
        }

    def prepare_main_competence(self, instance):
        sc = instance.learning_activity and instance.learning_activity.specific_competence
        mc = sc and sc.main_competence
        if not mc:
            return None
        return {
            "id": str(mc.id),
            "name": mc.name,
            "order": mc.order,
        }

    def prepare_specific_competence(self, instance):
        sc = instance.learning_activity and instance.learning_activity.specific_competence
        if not sc:
            return None
        return {
            "id": str(sc.id),
            "name": sc.name,
            "order": sc.order,
        }

    def prepare_learning_activity(self, instance):
        la = instance.learning_activity
        if not la:
            return None
        return {
            "id": str(la.id),
            "name": la.name,
            "order": la.order,
        }

    @classmethod
    def search(cls, using=None, index=None, **kwargs):
        if settings.DEBUG or not getattr(settings, 'ELASTICSEARCH_ENABLED', False):
            from search.utils.db_fallback import DBFallbackSearch
            return DBFallbackSearch(
                cls,
                SpecificLearningActivity.objects.select_related(
                    "learning_activity__specific_competence__main_competence__subject_version__subject",
                    "learning_activity__specific_competence__main_competence__subject_version__class_level",
                    "learning_activity__specific_competence__main_competence__subject_version__syllabus_version",
                    "learning_activity__specific_competence__main_competence",
                    "learning_activity__specific_competence",
                    "learning_activity",
                ),
                search_fields=("name", "method", "assessment_criteria", "teaching_aids"),
            )
        return super().search(using=using, index=index, **kwargs)