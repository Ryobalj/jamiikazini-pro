# search/documents/syllabus_document.py

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
    def prepare_subject(self, instance):
        subject = instance.learning_activity \
            .specific_competence \
            .main_competence \
            .subject_version \
            .subject

        return {
            "id": str(subject.id),
            "name": subject.name,
            "code": subject.code,
        }

    def prepare_class_level(self, instance):
        cl = instance.learning_activity \
            .specific_competence \
            .main_competence \
            .subject_version \
            .class_level

        return {
            "id": str(cl.id),
            "name": cl.name,
            "order": cl.order,
        }

    def prepare_syllabus_version(self, instance):
        sv = instance.learning_activity \
            .specific_competence \
            .main_competence \
            .subject_version \
            .syllabus_version

        return {
            "id": str(sv.id),
            "year": sv.year,
            "is_current": sv.is_current,
        }

    def prepare_subject_version(self, instance):
        sv = instance.learning_activity \
            .specific_competence \
            .main_competence \
            .subject_version

        return {
            "id": str(sv.id),
            "is_english": sv.is_english,
            "is_awali": sv.is_awali,
            "order": sv.order,
        }

    def prepare_main_competence(self, instance):
        mc = instance.learning_activity.specific_competence.main_competence
        return {
            "id": str(mc.id),
            "name": mc.name,
            "order": mc.order,
        }

    def prepare_specific_competence(self, instance):
        sc = instance.learning_activity.specific_competence
        return {
            "id": str(sc.id),
            "name": sc.name,
            "order": sc.order,
        }

    def prepare_learning_activity(self, instance):
        la = instance.learning_activity
        return {
            "id": str(la.id),
            "name": la.name,
            "order": la.order,
        }