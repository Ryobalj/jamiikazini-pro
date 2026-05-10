# kiini/models/location_mixin.py

from django.contrib.gis.db import models as gis_models

class LocationMixin(models.Model):
    """
    Mixin ya kuongeza location (GeoDjango PointField) kwenye model yoyote.
    """
    location = gis_models.PointField(geography=True, null=True, blank=True)

    class Meta:
        abstract = True