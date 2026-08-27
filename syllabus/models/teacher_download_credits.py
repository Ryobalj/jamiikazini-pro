# syllabus/models/teacher_download_credits.py

from django.conf import settings
from django.db import models


class TeacherDownloadCredits(models.Model):
    """
    Free-trial download counters, kept deliberately SEPARATE from
    TeacherWorkStation. A teacher can legitimately delete and recreate
    their workstation (e.g. changing schools) via
    TeacherWorkStationViewSet - if the counters lived there, that would
    also reset free downloads to zero every time, letting anyone farm
    unlimited free documents by deleting+recreating their own workstation
    in the same logged-in session (no re-registration needed). This row
    is tied to the User directly and only disappears if the account
    itself is deleted - not on every workstation change.
    """
    teacher = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="download_credits",
    )
    free_downloads_used = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Idadi ya nyaraka alizopakua bure kwa kila aina ya nyaraka "
            "(mfano {'SCHEME': 1, 'EXAM_RESULTS': 2}) - kila aina ina "
            "kikomo chake tofauti (angalia "
            "subscription_service.FREE_DOWNLOAD_LIMITS)."
        ),
    )

    def __str__(self):
        return f"Download credits for {self.teacher}"
