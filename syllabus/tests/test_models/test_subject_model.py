# jammikazini/syllabus/tests/test_models/test_subject_model.py

from django.test import TestCase
from syllabus.models.subject import Subject


class TestSubjectModel(TestCase):

    def test_auto_generate_first_code(self):
        subject = Subject.objects.create(name="Mathematics")
        assert subject.code == "JSS001"

    def test_auto_generate_next_code(self):
        Subject.objects.create(name="Physics")                # -> JSS001
        subject2 = Subject.objects.create(name="Chemistry")   # -> JSS002
        assert subject2.code == "JSS002"

    def test_preserve_manual_code(self):
        subject = Subject.objects.create(name="Biology", code="BIO123")
        assert subject.code == "BIO123"

    def test_str_representation(self):
        subject = Subject.objects.create(name="Geography")
        assert str(subject) == "Geography (JSS001)"

    def test_ordering_by_name(self):
        Subject.objects.create(name="Zulu")
        Subject.objects.create(name="English")
        Subject.objects.create(name="Kiswahili")

        subjects = list(Subject.objects.all())
        names = [s.name for s in subjects]

        assert names == ["English", "Kiswahili", "Zulu"]