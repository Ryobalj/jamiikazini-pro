# logistics/models/transport_request.py

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import Distance as D
from django.contrib.gis.db.models.functions import Distance

from django.conf import settings
from kiini.models.base import UUIDModel, TimeStampedModel
from businesses.models.business import Business
from kiini.models.institution import Institution
from logistics.choices import TransportTypeChoices, TransportRequestStatus
from django.contrib.gis.db.models.functions import Distance


class TransportRequest(UUIDModel, TimeStampedModel):
    REQUESTOR_TYPE_CHOICES = (
        ("business", _("Business")),
        ("institution", _("Institution")),
        ("individual", _("Individual")),
    )

    requestor_type = models.CharField(
        max_length=20, choices=REQUESTOR_TYPE_CHOICES, verbose_name=_("Requestor Type")
    )
    business = models.ForeignKey(
        Business, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="transport_requests", verbose_name=_("Business")
    )
    institution = models.ForeignKey(
        Institution, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="transport_requests", verbose_name=_("Institution")
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="standalone_transport_requests", verbose_name=_("Requested By"),
        help_text=_("Mtu binafsi aliyeomba huduma hii ya usafiri moja kwa moja - "
                     "bila kuhusiana na ununuzi wa bidhaa (requestor_type='individual')."),
    )

    package_description = models.TextField(verbose_name=_("Package Description"))
    weight_kg = models.FloatField(verbose_name=_("Weight (kg)"))
    volume_cbm = models.FloatField(null=True, blank=True, verbose_name=_("Volume (m³)"))
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Estimated Value"))

    suggested_transport_type = models.CharField(
        max_length=30, choices=TransportTypeChoices.choices, verbose_name=_("Suggested Transport Type")
    )

    pickup_location = gis_models.PointField(verbose_name=_("Pickup Location"))
    dropoff_location = gis_models.PointField(verbose_name=_("Dropoff Location"))

    pickup_address_text = models.CharField(max_length=255, verbose_name=_("Pickup Address Text"))
    dropoff_address_text = models.CharField(max_length=255, verbose_name=_("Dropoff Address Text"))

    origin_country = models.CharField(max_length=100, null=True, blank=True)
    destination_country = models.CharField(max_length=100, null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=TransportRequestStatus.choices,
        default=TransportRequestStatus.PENDING, verbose_name=_("Request Status")
    )
    is_accepted = models.BooleanField(default=False, verbose_name=_("Is Accepted"))

    requested_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Requested At"))
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Expires At"))

    order = models.OneToOneField(
        "businesses.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transport_request",
        verbose_name=_("Order"),
        help_text=_("Order husika ikiwa ombi hili la usafiri limetokana na ununuzi wa bidhaa."),
    )
    estimated_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Estimated Fare"),
    )

    class Meta:
        verbose_name = _("Transport Request")
        verbose_name_plural = _("Transport Requests")
        ordering = ['created_at']

    def __str__(self):
        who = self.business.name if self.requestor_type == "business" and self.business else (
            self.institution.name if self.institution else "Unknown"
        )
        return f"Transport Request from {who} ({self.package_description[:20]}...)"

    def calculate_distance_km(self):
        """Calculate geodesic distance between pickup and dropoff."""
        if self.pickup_location and self.dropoff_location:
            return self.pickup_location.distance(self.dropoff_location) * 100  # deg to approx km
        return 0

    def suggest_transport_type(self):
        """
        Suggest transport type based on weight, volume, distance, and international
        factors. Delegates the actual suitability rules to
        logistics.services.weight_bands so this can never drift from the rules
        the delivery-quote endpoint and order-creation validation enforce.
        """
        from logistics.services.weight_bands import suitable_vehicle_types

        weight = self.weight_kg
        volume = self.volume_cbm
        distance_km = self.calculate_distance_km()
        suitable = suitable_vehicle_types(weight, distance_km, volume)

        if (
            self.origin_country
            and self.destination_country
            and self.origin_country != self.destination_country
            and TransportTypeChoices.SHIP in suitable
        ):
            return TransportTypeChoices.SHIP

        priority = [
            TransportTypeChoices.BODA_BODA,
            TransportTypeChoices.BAJAJI,
            TransportTypeChoices.SUZUKI_CARRY,
            TransportTypeChoices.TUK_TUK,
            TransportTypeChoices.PUBLIC_TRANSPORT,
            TransportTypeChoices.BUS,
            TransportTypeChoices.CANTER,
            TransportTypeChoices.FUSO,
            TransportTypeChoices.SCANIA,
            TransportTypeChoices.TRAIN,
            TransportTypeChoices.SHIP,
            TransportTypeChoices.AIR,
        ]
        for vehicle_type in priority:
            if vehicle_type in suitable:
                return vehicle_type
        return TransportTypeChoices.AIR

    def get_recommended_vehicles(self, max_distance_km=50):
        from logistics.models import Vehicle

        """
        Pata magari yanayopendekezwa kwa ombi hili la usafiri.
        Inazingatia aina ya usafiri, uzito, ujazo, uthibitisho, na umbali.
        """
        weight = self.weight_kg
        volume = self.volume_cbm or 0
        pickup_point = self.pickup_location
        suggested_type = self.suggested_transport_type

        vehicles = Vehicle.objects.filter(
            vehicle_type=suggested_type,
            is_active=True,
            active_driver__isnull=False
        ).annotate(
            distance=Distance("provider__location", pickup_point)
        ).filter(
            distance__lte=max_distance_km * 1000  # kilometers to meters
        ).order_by("distance")

        suitable = []
        for v in vehicles:
            if v.is_fully_verified and (
                (v.capacity_kg is None or v.capacity_kg >= weight) and
                (v.volume_cbm is None or v.volume_cbm >= volume)
            ):
                suitable.append(v)

        return suitable