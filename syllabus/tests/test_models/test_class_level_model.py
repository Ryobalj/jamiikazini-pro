# syllabus/tests/test_models/test_class_level_model.py

import pytest
from django.db import models
from syllabus.models.class_level import ClassLevel

@pytest.mark.django_db
class TestClassLevelModel:

    def test_create_class_level_auto_order(self):
        # Hakuna records, order lazima iwe 1
        cl = ClassLevel.objects.create(name="III")
        assert cl.order == 1
        assert cl.name == "III"

        # Create nyingine, order lazima iende +1
        cl2 = ClassLevel.objects.create(name="IV")
        assert cl2.order == 2

    def test_update_class_level(self):
        cl = ClassLevel.objects.create(name="V")
        cl.description = "Darasa la tano"
        cl.save()
        updated = ClassLevel.objects.get(id=cl.id)
        assert updated.description == "Darasa la tano"
        # order haibadiliki
        assert updated.order == cl.order

    def test_delete_class_level(self):
        cl = ClassLevel.objects.create(name="VI")
        cl_id = cl.id
        cl.delete()
        with pytest.raises(ClassLevel.DoesNotExist):
            ClassLevel.objects.get(id=cl_id)

    def test_str_method(self):
        cl = ClassLevel.objects.create(name="VII")
        assert str(cl) == "VII"

    def test_order_with_existing_max(self):
        # Create multiple to check max aggregation
        ClassLevel.objects.create(name="VIII")
        ClassLevel.objects.create(name="IX")
        cl = ClassLevel.objects.create(name="X")
        max_order = ClassLevel.objects.aggregate(models.Max('order'))['order__max']
        assert cl.order == max_order